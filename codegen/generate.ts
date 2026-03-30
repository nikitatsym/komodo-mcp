/**
 * Codegen: generate _generated.py from komodo_client TypeScript types.
 *
 * Uses the TypeScript Compiler API for reliable type resolution —
 * no regex parsing of interfaces, generics, or JSDoc.
 *
 * Usage: npx tsx generate.ts
 */

import * as ts from "typescript";
import { writeFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const TYPES_PATH = join(
  __dirname,
  "node_modules/komodo_client/src/types.ts"
);
const OUT_PATH = join(__dirname, "../src/komodo_mcp/_generated.py");

// ── Load program ─────────────────────────────────────────────────────────

const program = ts.createProgram([TYPES_PATH], {
  target: ts.ScriptTarget.ESNext,
  module: ts.ModuleKind.ESNext,
  strict: true,
});
const sourceFile = program.getSourceFile(TYPES_PATH)!;
const checker = program.getTypeChecker();

// ── Step 1: Extract operations from discriminated unions ─────────────────

type Endpoint = "read" | "write" | "execute";

const ops: Map<string, { endpoint: Endpoint; iface: ts.InterfaceType }> =
  new Map();

function extractOps(unionName: string, endpoint: Endpoint) {
  const sym = checker.getSymbolsInScope(
    sourceFile,
    ts.SymbolFlags.TypeAlias
  ).find((s) => s.name === unionName);
  if (!sym) throw new Error(`Union ${unionName} not found`);

  // Resolve the type alias to its underlying union type
  const decl = sym.declarations?.[0];
  if (!decl || !ts.isTypeAliasDeclaration(decl))
    throw new Error(`${unionName} is not a type alias`);
  const type = checker.getTypeFromTypeNode(decl.type);
  if (!type.isUnion()) throw new Error(`${unionName} is not a union`);

  for (const member of type.types) {
    // Each member: { type: "OpName", params: OpInterface }
    const typeProp = member.getProperty("type");
    const paramsProp = member.getProperty("params");
    if (!typeProp || !paramsProp) continue;

    const typeType = checker.getTypeOfSymbol(typeProp);
    if (!typeType.isStringLiteral()) continue;
    const opName = typeType.value;

    const paramsType = checker.getTypeOfSymbol(paramsProp);
    if (paramsType.getFlags() & ts.TypeFlags.Object) {
      ops.set(opName, {
        endpoint,
        iface: paramsType as ts.InterfaceType,
      });
    }
  }
}

extractOps("ReadRequest", "read");
extractOps("WriteRequest", "write");
extractOps("ExecuteRequest", "execute");

console.log(`Found ${ops.size} operations total`);

// ── Step 2: Type mapping ─────────────────────────────────────────────────

function toSnakeCase(name: string): string {
  return name
    .replace(/([A-Z]+)([A-Z][a-z])/g, "$1_$2")
    .replace(/([a-z\d])([A-Z])/g, "$1_$2")
    .toLowerCase();
}

/** Get string literal values from a union of string literals (enum). */
function getStringLiteralValues(type: ts.Type): string[] | null {
  if (type.isUnion()) {
    const vals: string[] = [];
    for (const m of type.types) {
      if (m.isStringLiteral()) {
        vals.push(m.value);
      }
    }
    if (vals.length > 0 && vals.length === type.types.length) {
      return vals;
    }
  }
  if (type.isStringLiteral()) {
    return [type.value];
  }
  return null;
}

/** Check if a type is ResourceQuery<T>. Returns base + specific fields. */
function resolveResourceQuery(
  type: ts.Type
): { baseFields: ts.Symbol[]; specificFields: ts.Symbol[] } | null {
  const sym = type.getSymbol() || type.aliasSymbol;
  // Follow alias to see if it resolves to ResourceQuery<T>
  const targetType =
    type.aliasSymbol
      ? checker.getDeclaredTypeOfSymbol(type.aliasSymbol)
      : type;
  const targetSym = targetType.getSymbol();
  if (!targetSym) return null;

  // Check if base interface is ResourceQuery
  // Walk alias chain
  let resolved = type;
  if (type.aliasSymbol) {
    const aliasType = checker.getTypeOfSymbol(type.aliasSymbol);
    // Try type arguments from the alias
  }

  // Check symbol name directly or through alias
  const props = checker.getPropertiesOfType(type);
  const propNames = new Set(props.map((p) => p.name));

  // ResourceQuery has: names?, templates?, tags?, tag_behavior?, specific?
  if (
    propNames.has("tags") &&
    propNames.has("tag_behavior") &&
    propNames.has("specific")
  ) {
    const baseFields = props.filter((p) => p.name !== "specific");
    // Resolve the specific field's type to get its properties
    const specificProp = props.find((p) => p.name === "specific");
    let specificFields: ts.Symbol[] = [];
    if (specificProp) {
      const specificType = checker.getTypeOfSymbol(specificProp).getNonNullableType();
      specificFields = checker.getPropertiesOfType(specificType);
    }
    return { baseFields, specificFields };
  }
  return null;
}

/** Check if type is ResourceTarget or UserTarget. */
function getTargetKind(
  type: ts.Type
): "resource" | "user" | null {
  // These are discriminated unions: { type: "Server", id: string } | ...
  if (!type.isUnion()) return null;
  const props = new Set<string>();
  for (const member of type.types) {
    for (const p of checker.getPropertiesOfType(member)) {
      props.add(p.name);
    }
  }
  if (!props.has("type") || !props.has("id")) return null;

  // Check discriminant values to distinguish Resource vs User
  for (const member of type.types) {
    const typeProp = member.getProperty("type");
    if (!typeProp) continue;
    const t = checker.getTypeOfSymbol(typeProp);
    if (t.isStringLiteral()) {
      if (t.value === "Server" || t.value === "Stack" || t.value === "System")
        return "resource";
      if (t.value === "User" || t.value === "UserGroup") return "user";
    }
  }
  return null;
}

interface PyParam {
  name: string;
  type: string; // Python type annotation
  required: boolean;
}

interface QueryReassembly {
  kind: "query";
  originalName: string;
  baseFieldNames: string[];
  specificFieldNames: string[];
}

interface TargetReassembly {
  kind: "target";
  originalName: string;
  typeName: string;
  idName: string;
  required: boolean;
}

type Reassembly = QueryReassembly | TargetReassembly;

/**
 * Convert a TS type to Python type string.
 * Returns a Literal[...] for string enums.
 */
function tsPyType(type: ts.Type): string {
  // Unwrap T | undefined for optional fields
  const t = type.getNonNullableType();

  // Boolean
  if (t.getFlags() & ts.TypeFlags.Boolean) return "bool";
  if (t.getFlags() & ts.TypeFlags.BooleanLiteral) return "bool";

  // String
  if (t.getFlags() & ts.TypeFlags.String) return "str";
  if (t.isStringLiteral()) return "str";

  // Number
  if (t.getFlags() & ts.TypeFlags.Number) return "int";
  if (t.isNumberLiteral()) return "int";

  // Check for string literal union (enum) → Literal
  const litVals = getStringLiteralValues(t);
  if (litVals) {
    return `Literal[${litVals.map((v) => `"${v}"`).join(", ")}]`;
  }

  // Union with non-all-string-literal members (e.g. PermissionLevel | PermissionLevelAndSpecifics)
  if (t.isUnion()) {
    // Check if it's bool (true | false union)
    const isBool = t.types.every(
      (tt) => tt.getFlags() & ts.TypeFlags.BooleanLiteral
    );
    if (isBool) return "bool";
    return "dict";
  }

  // Array
  if (checker.isArrayType(t)) {
    const typeArgs = checker.getTypeArguments(t as ts.TypeReference);
    if (typeArgs.length === 1) {
      return `list[${tsPyType(typeArgs[0])}]`;
    }
    return "list";
  }

  // Object / interface — default to dict
  if (t.getFlags() & ts.TypeFlags.Object) return "dict";

  return "dict";
}

/**
 * Resolve config interface for documentation.
 * For Partial<StackConfig> → get StackConfig fields.
 */
function resolveConfigFields(
  type: ts.Type
): { name: string; pyType: string }[] | null {
  const props = checker.getPropertiesOfType(type);
  if (props.length < 3) return null; // Not a config object

  // Check if this looks like a config (many optional fields)
  const optCount = props.filter((p) =>
    (p.getFlags() & ts.SymbolFlags.Optional) ||
    p.declarations?.some(
      (d) => ts.isPropertySignature(d) && !!d.questionToken
    )
  ).length;
  if (optCount < 3) return null;

  return props.slice(0, 15).map((p) => ({
    name: p.name,
    pyType: tsPyType(checker.getTypeOfSymbol(p)),
  }));
}

/**
 * Process an operation interface: flatten queries/targets, resolve types.
 */
function processOperation(
  opName: string,
  type: ts.InterfaceType
): {
  params: PyParam[];
  reassemblies: Reassembly[];
  directRequired: { name: string; pyType: string }[];
  directOptional: { name: string; pyType: string }[];
  configDocs: string[];
} {
  const params: PyParam[] = [];
  const reassemblies: Reassembly[] = [];
  const directRequired: { name: string; pyType: string }[] = [];
  const directOptional: { name: string; pyType: string }[] = [];
  const configDocs: string[] = [];

  const props = checker.getPropertiesOfType(type);

  for (const prop of props) {
    const rawPropType = checker.getTypeOfSymbol(prop);
    const isOptional =
      (prop.getFlags() & ts.SymbolFlags.Optional) !== 0 ||
      prop.declarations?.some(
        (d) => ts.isPropertySignature(d) && !!d.questionToken
      ) ||
      false;
    // Unwrap optional (T | undefined) to get the real type
    const propType = rawPropType.getNonNullableType();

    // Try ResourceQuery expansion
    const queryInfo = resolveResourceQuery(propType);
    if (queryInfo) {
      const baseNames: string[] = [];
      const specificNames: string[] = [];

      for (const bf of queryInfo.baseFields) {
        const bfType = checker.getTypeOfSymbol(bf);
        params.push({
          name: bf.name,
          type: tsPyType(bfType),
          required: false,
        });
        baseNames.push(bf.name);
      }
      for (const sf of queryInfo.specificFields) {
        const sfType = checker.getTypeOfSymbol(sf);
        params.push({
          name: sf.name,
          type: tsPyType(sfType),
          required: false,
        });
        specificNames.push(sf.name);
      }
      reassemblies.push({
        kind: "query",
        originalName: prop.name,
        baseFieldNames: baseNames,
        specificFieldNames: specificNames,
      });
      continue;
    }

    // Try ResourceTarget / UserTarget expansion
    const targetKind = getTargetKind(propType);
    if (targetKind) {
      const prefix = prop.name;
      const typeName = `${prefix}_type`;
      const idName = `${prefix}_id`;

      // Collect all discriminant values from the union members
      const allTargetTypes: string[] = [];
      if (propType.isUnion()) {
        for (const m of propType.types) {
          const tp = m.getProperty("type");
          if (tp) {
            const tt = checker.getTypeOfSymbol(tp);
            if (tt.isStringLiteral()) allTargetTypes.push(tt.value);
          }
        }
      }

      const litType =
        allTargetTypes.length > 0
          ? `Literal[${allTargetTypes.map((v) => `"${v}"`).join(", ")}]`
          : "str";

      params.push({ name: typeName, type: litType, required: !isOptional });
      params.push({ name: idName, type: "str", required: !isOptional });
      reassemblies.push({
        kind: "target",
        originalName: prop.name,
        typeName,
        idName,
        required: !isOptional,
      });
      continue;
    }

    // Regular field
    const pyType = tsPyType(propType);
    params.push({ name: prop.name, type: pyType, required: !isOptional });

    if (isOptional) {
      directOptional.push({ name: prop.name, pyType });
    } else {
      directRequired.push({ name: prop.name, pyType });
    }

    // Config field documentation for dict params
    if (pyType === "dict") {
      const fields = resolveConfigFields(propType);
      if (fields && fields.length > 0) {
        const fieldStr = fields
          .map((f) => `${f.name} (${f.pyType})`)
          .join(", ");
        const suffix = fields.length >= 15 ? ", ..." : "";
        configDocs.push(`${prop.name} fields: ${fieldStr}${suffix}`);
      }
    }
  }

  return { params, reassemblies, directRequired, directOptional, configDocs };
}

// ── Step 3: Generate Python ──────────────────────────────────────────────

const pyLines: string[] = [
  "# GENERATED by codegen/generate.ts — DO NOT EDIT",
  "from __future__ import annotations",
  "",
  "from typing import Literal",
  "",
  "from ._helpers import _ok, _get_client",
  "",
  "",
];

const sortedOps = [...ops.entries()].sort((a, b) => {
  const order: Record<string, number> = { read: 0, write: 1, execute: 2 };
  const eo = order[a[1].endpoint] - order[b[1].endpoint];
  if (eo !== 0) return eo;
  return a[0].localeCompare(b[0]);
});

let currentEndpoint = "";
let flattenedCount = 0;

for (const [opName, { endpoint, iface }] of sortedOps) {
  if (endpoint !== currentEndpoint) {
    if (currentEndpoint) pyLines.push("");
    pyLines.push(`# ── ${endpoint} ${"─".repeat(68 - endpoint.length)}`);
    pyLines.push("");
    currentEndpoint = endpoint;
  }

  const fnName = toSnakeCase(opName);
  const { params, reassemblies, directRequired, directOptional, configDocs } =
    processOperation(opName, iface);

  if (reassemblies.length > 0) flattenedCount++;

  // Build signature
  const sigParts: string[] = [];
  const requiredParams = params.filter((p) => p.required);
  const optionalParams = params.filter((p) => !p.required);

  for (const p of requiredParams) {
    sigParts.push(`${p.name}: ${p.type}`);
  }
  for (const p of optionalParams) {
    sigParts.push(`${p.name}: ${p.type} | None = None`);
  }

  const sig =
    sigParts.length > 0
      ? `def ${fnName}(${sigParts.join(", ")}):`
      : `def ${fnName}():`;

  // Docstring — just the operation name, no JSDoc
  pyLines.push(sig);
  if (configDocs.length > 0) {
    pyLines.push(`    """${opName}.`);
    pyLines.push("");
    for (const cd of configDocs) {
      pyLines.push(`    ${cd}`);
    }
    pyLines.push(`    """`);
  } else {
    pyLines.push(`    """${opName}."""`);
  }

  // Function body
  if (params.length === 0) {
    pyLines.push(
      `    return _ok(_get_client().${endpoint}("${opName}"))`
    );
  } else if (reassemblies.length > 0) {
    // Has flattened params
    if (directRequired.length > 0) {
      const reqParts = directRequired
        .map((f) => `"${f.name}": ${f.name}`)
        .join(", ");
      pyLines.push(`    params: dict = {${reqParts}}`);
    } else {
      pyLines.push(`    params: dict = {}`);
    }

    for (const f of directOptional) {
      pyLines.push(`    if ${f.name} is not None:`);
      pyLines.push(`        params["${f.name}"] = ${f.name}`);
    }

    for (const r of reassemblies) {
      if (r.kind === "query") {
        pyLines.push(`    _query: dict = {}`);
        for (const bn of r.baseFieldNames) {
          pyLines.push(`    if ${bn} is not None:`);
          pyLines.push(`        _query["${bn}"] = ${bn}`);
        }
        if (r.specificFieldNames.length > 0) {
          pyLines.push(`    _specific: dict = {}`);
          for (const sn of r.specificFieldNames) {
            pyLines.push(`    if ${sn} is not None:`);
            pyLines.push(`        _specific["${sn}"] = ${sn}`);
          }
          pyLines.push(`    if _specific:`);
          pyLines.push(`        _query["specific"] = _specific`);
        }
        pyLines.push(`    if _query:`);
        pyLines.push(`        params["${r.originalName}"] = _query`);
      } else if (r.kind === "target") {
        if (r.required) {
          pyLines.push(
            `    params["${r.originalName}"] = {"type": ${r.typeName}, "id": ${r.idName}}`
          );
        } else {
          pyLines.push(
            `    if ${r.typeName} is not None and ${r.idName} is not None:`
          );
          pyLines.push(
            `        params["${r.originalName}"] = {"type": ${r.typeName}, "id": ${r.idName}}`
          );
        }
      }
    }

    pyLines.push(
      `    return _ok(_get_client().${endpoint}("${opName}", params or None))`
    );
  } else {
    // No flattening
    if (requiredParams.length > 0 && optionalParams.length > 0) {
      const reqParts = requiredParams
        .map((p) => `"${p.name}": ${p.name}`)
        .join(", ");
      pyLines.push(`    params: dict = {${reqParts}}`);
      for (const p of optionalParams) {
        pyLines.push(`    if ${p.name} is not None:`);
        pyLines.push(`        params["${p.name}"] = ${p.name}`);
      }
      pyLines.push(
        `    return _ok(_get_client().${endpoint}("${opName}", params))`
      );
    } else if (requiredParams.length > 0) {
      const parts = requiredParams
        .map((p) => `"${p.name}": ${p.name}`)
        .join(", ");
      pyLines.push(
        `    return _ok(_get_client().${endpoint}("${opName}", {${parts}}))`
      );
    } else {
      pyLines.push("    params: dict = {}");
      for (const p of optionalParams) {
        pyLines.push(`    if ${p.name} is not None:`);
        pyLines.push(`        params["${p.name}"] = ${p.name}`);
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
const output = pyLines
  .join("\n")
  .replace(/\n{3,}/g, "\n\n\n")
  .trimEnd() + "\n";
writeFileSync(OUT_PATH, output);
console.log(`Wrote ${OUT_PATH}`);
console.log(
  `  ${sortedOps.filter(([, o]) => o.endpoint === "read").length} read, ` +
    `${sortedOps.filter(([, o]) => o.endpoint === "write").length} write, ` +
    `${sortedOps.filter(([, o]) => o.endpoint === "execute").length} execute`
);
console.log(`  ${flattenedCount} operations with flattened parameters`);
