/**
 * Codegen: parse komodo_client TypeScript types and generate _generated.py.
 *
 * Reads the discriminated unions (ReadRequest, WriteRequest, ExecuteRequest)
 * and corresponding param interfaces from komodo_client/src/types.ts,
 * then outputs Python functions that call the Komodo API via _helpers.
 *
 * Usage: npx tsx generate.ts
 */

import { readFileSync, writeFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const TYPES_PATH = join(
  __dirname,
  "node_modules/komodo_client/src/types.ts"
);
const OUT_PATH = join(__dirname, "../src/komodo_mcp/_generated.py");

const src = readFileSync(TYPES_PATH, "utf-8");

// ── Step 1: Extract operations from discriminated unions ─────────────────

type Endpoint = "read" | "write" | "execute";

const ops: Map<string, Endpoint> = new Map();

function extractUnion(name: string, endpoint: Endpoint) {
  // Match: export type ReadRequest = \n\t| { type: "OpName", params: OpName }\n...;
  const re = new RegExp(
    `export type ${name} =\\s*([\\s\\S]*?);`,
    "m"
  );
  const m = src.match(re);
  if (!m) throw new Error(`Union ${name} not found`);
  const body = m[1];
  for (const line of body.split("\n")) {
    const lm = line.match(/\{ type: "(\w+)", params: \w+ \}/);
    if (lm) ops.set(lm[1], endpoint);
  }
}

extractUnion("ReadRequest", "read");
extractUnion("WriteRequest", "write");
extractUnion("ExecuteRequest", "execute");

console.log(`Found ${ops.size} operations total`);

// ── Step 2: Parse interfaces ─────────────────────────────────────────────

interface Field {
  name: string;
  tsType: string;
  optional: boolean;
  doc: string; // first line of JSDoc
}

interface ParsedInterface {
  name: string;
  doc: string; // JSDoc above the interface
  fields: Field[];
}

const interfaces: Map<string, ParsedInterface> = new Map();

// Pre-process: collect all interfaces with their positions
const ifaceRegex =
  /(?:\/\*\*[\s\S]*?\*\/\s*)?export interface (\w+)(?:<[^>]*>)?\s*\{/g;

let ifMatch: RegExpExecArray | null;
while ((ifMatch = ifaceRegex.exec(src)) !== null) {
  const ifaceName = ifMatch[1];
  const startPos = ifMatch.index;
  const bodyStart = src.indexOf("{", ifMatch.index + ifMatch[0].length - 1);

  // Find matching closing brace
  let depth = 1;
  let pos = bodyStart + 1;
  while (depth > 0 && pos < src.length) {
    if (src[pos] === "{") depth++;
    else if (src[pos] === "}") depth--;
    pos++;
  }
  const bodyEnd = pos - 1;
  const body = src.slice(bodyStart + 1, bodyEnd);

  // Extract JSDoc above the interface
  const before = src.slice(Math.max(0, startPos - 500), startPos);
  let ifaceDoc = "";
  const docMatch = before.match(/\/\*\*\s*([\s\S]*?)\s*\*\/\s*$/);
  if (docMatch) {
    ifaceDoc = docMatch[1]
      .replace(/^\s*\*\s?/gm, "")
      .split("\n")[0]
      .trim();
  }

  // Parse fields
  const fields: Field[] = [];
  // Split by lines and parse each field
  const lines = body.split("\n");
  let currentDoc = "";

  for (const line of lines) {
    const trimmed = line.trim();

    // Accumulate JSDoc
    if (trimmed.startsWith("/**")) {
      // Single-line JSDoc: /** ... */
      const singleDoc = trimmed.match(/\/\*\*\s*(.*?)\s*\*\//);
      if (singleDoc) {
        currentDoc = singleDoc[1];
        continue;
      }
      currentDoc = "";
      continue;
    }
    if (trimmed.startsWith("*")) {
      if (trimmed === "*/") continue;
      const docLine = trimmed.replace(/^\*\s?/, "").trim();
      if (docLine && !currentDoc) currentDoc = docLine;
      continue;
    }

    // Field: name?: Type;
    const fieldMatch = trimmed.match(
      /^(\w+)(\?)?:\s*(.+?);?\s*$/
    );
    if (fieldMatch) {
      fields.push({
        name: fieldMatch[1],
        tsType: fieldMatch[3].replace(/;$/, "").trim(),
        optional: !!fieldMatch[2],
        doc: currentDoc,
      });
      currentDoc = "";
    }
  }

  interfaces.set(ifaceName, { name: ifaceName, doc: ifaceDoc, fields });
}

console.log(`Parsed ${interfaces.size} interfaces`);

// ── Step 3: Type mapping ─────────────────────────────────────────────────

function tsPyType(tsType: string): string {
  // Remove trailing semicolons
  tsType = tsType.replace(/;$/, "").trim();

  // Primitive types
  if (tsType === "string") return "str";
  if (tsType === "number" || tsType === "I64") return "int";
  if (tsType === "boolean") return "bool";

  // Arrays
  if (tsType.endsWith("[]")) {
    const inner = tsType.slice(0, -2);
    const pyInner = tsPyType(inner);
    return `list[${pyInner}]`;
  }

  // JsonObject, any
  if (tsType === "JsonObject" || tsType === "any" || tsType === "JsonValue")
    return "dict";

  // Union types with | — check for PermissionLevelAndSpecifics | PermissionLevel
  if (tsType.includes("|")) return "dict";

  // ResourceTarget["type"] (used in RunSync for resource_type)
  if (tsType.includes('["type"]') || tsType.includes("['type']"))
    return "str";

  // Enum types (serialize as strings)
  // Named types that are enums or complex objects → str for enums, dict for objects
  const knownEnums = new Set([
    "TerminationSignal",
    "Timelength",
    "SearchCombinator",
    "SeverityLevel",
    "TerminalRecreateMode",
    "TagQueryBehavior",
    "PermissionLevel",
  ]);
  if (knownEnums.has(tsType)) return "str";

  // Everything else (named interfaces, config objects, query objects) → dict
  return "dict";
}

// ── Step 4: Generate Python ──────────────────────────────────────────────

function toSnakeCase(name: string): string {
  // PascalCase → snake_case
  return name
    .replace(/([A-Z]+)([A-Z][a-z])/g, "$1_$2")
    .replace(/([a-z\d])([A-Z])/g, "$1_$2")
    .toLowerCase();
}

const pyLines: string[] = [
  "# GENERATED by codegen/generate.ts — DO NOT EDIT",
  "from __future__ import annotations",
  "",
  "from ._helpers import _ok, _get_client",
  "",
  "",
];

// Sort operations by endpoint then name for readability
const sortedOps = [...ops.entries()].sort((a, b) => {
  const endpointOrder: Record<string, number> = {
    read: 0,
    write: 1,
    execute: 2,
  };
  const eo = endpointOrder[a[1]] - endpointOrder[b[1]];
  if (eo !== 0) return eo;
  return a[0].localeCompare(b[0]);
});

let currentEndpoint = "";

for (const [opName, endpoint] of sortedOps) {
  const iface = interfaces.get(opName);
  if (!iface) {
    console.warn(`  WARNING: No interface found for ${opName}, skipping`);
    continue;
  }

  if (endpoint !== currentEndpoint) {
    if (currentEndpoint) pyLines.push("");
    pyLines.push(
      `# ── ${endpoint} ${"─".repeat(68 - endpoint.length)}`
    );
    pyLines.push("");
    currentEndpoint = endpoint;
  }

  const fnName = toSnakeCase(opName);
  const fields = iface.fields;

  // Build function signature
  const params: string[] = [];
  const requiredFields = fields.filter((f) => !f.optional);
  const optionalFields = fields.filter((f) => f.optional);

  for (const f of requiredFields) {
    params.push(`${f.name}: ${tsPyType(f.tsType)}`);
  }
  for (const f of optionalFields) {
    params.push(`${f.name}: ${tsPyType(f.tsType)} | None = None`);
  }

  const sig =
    params.length > 0
      ? `def ${fnName}(${params.join(", ")}) -> str:`
      : `def ${fnName}() -> str:`;

  // Build docstring
  let doc = iface.doc || `${opName}.`;
  // Clean up Response: [...] references
  doc = doc.replace(/\s*Response:\s*\[.*?\]\.?/g, "").trim();
  if (!doc.endsWith(".")) doc += ".";

  // Add field docs
  const fieldDocs: string[] = [];
  for (const f of fields) {
    if (f.doc) {
      fieldDocs.push(`${f.name}: ${f.doc}`);
    }
  }

  pyLines.push(sig);
  if (fieldDocs.length > 0) {
    pyLines.push(`    """${doc}`);
    pyLines.push("");
    for (const fd of fieldDocs) {
      pyLines.push(`    ${fd}`);
    }
    pyLines.push(`    """`);
  } else {
    pyLines.push(`    """${doc}"""`);
  }

  // Build function body
  if (fields.length === 0) {
    pyLines.push(
      `    return _ok(_get_client().${endpoint}("${opName}"))`
    );
  } else {
    // Build params dict
    if (requiredFields.length > 0 && optionalFields.length > 0) {
      // Mix of required and optional
      const reqParts = requiredFields
        .map((f) => `"${f.name}": ${f.name}`)
        .join(", ");
      pyLines.push(`    params: dict = {${reqParts}}`);
      for (const f of optionalFields) {
        pyLines.push(`    if ${f.name} is not None:`);
        pyLines.push(`        params["${f.name}"] = ${f.name}`);
      }
      pyLines.push(
        `    return _ok(_get_client().${endpoint}("${opName}", params))`
      );
    } else if (requiredFields.length > 0) {
      // All required
      const parts = requiredFields
        .map((f) => `"${f.name}": ${f.name}`)
        .join(", ");
      pyLines.push(
        `    return _ok(_get_client().${endpoint}("${opName}", {${parts}}))`
      );
    } else {
      // All optional
      pyLines.push("    params: dict = {}");
      for (const f of optionalFields) {
        pyLines.push(`    if ${f.name} is not None:`);
        pyLines.push(`        params["${f.name}"] = ${f.name}`);
      }
      pyLines.push(
        `    return _ok(_get_client().${endpoint}("${opName}", params or None))`
      );
    }
  }

  pyLines.push("");
  pyLines.push("");
}

// Write output
const output = pyLines.join("\n").replace(/\n{3,}/g, "\n\n\n").trimEnd() + "\n";
writeFileSync(OUT_PATH, output);
console.log(`Wrote ${OUT_PATH}`);
console.log(
  `  ${sortedOps.filter(([, e]) => e === "read").length} read, ` +
    `${sortedOps.filter(([, e]) => e === "write").length} write, ` +
    `${sortedOps.filter(([, e]) => e === "execute").length} execute`
);
