/**
 * AegisHarness bundle for DeepSeek Harness (`dsh`).
 *
 * Registers the nine `/aegis-*` skills as runtime skills through `ctx.skills`, so a
 * profile that mounts this bundle discovers them without copying anything into
 * `$DSH_HOME/skills`. Skill bodies stay single-sourced: they are read from the shipped
 * `hosts/deepseek-dsh/skills/_/SKILL.md` shims, and every relative resource the body
 * mentions resolves against the installed package root instead of the workspace.
 *
 * @module @eliterncn/aegisharness-dsh
 */
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

/** Cordis plugin name shown in profile diagnostics. */
const name = 'aegisharness'

/** The registry this bundle contributes to; it owns no other service. */
const inject = ['skills']

/** Installed package root; resources resolve against it, never the workspace. */
const PACKAGE_ROOT = dirname(dirname(fileURLToPath(import.meta.url)))
const SKILLS_ROOT = join(PACKAGE_ROOT, 'hosts', 'deepseek-dsh', 'skills')
const SKILL_PREFIX = 'aegis-'

/** The public contract owns the command list; a missing shim is a packaging bug. */
const COMMANDS = Object.freeze([
  'init',
  'propose',
  'apply',
  'archive',
  'bug-fix',
  'ut',
  'update',
  'status',
  'config',
])

/**
 * Read one skill shim: its `name` and `description` frontmatter plus the body.
 * @param {string} file - absolute path of a `SKILL.md`.
 * @returns {{ fields: Record<string, string>, body: string }} parsed shim.
 */
function parseSkillFile(file) {
  const text = readFileSync(file, 'utf8')
  if (!text.startsWith('---\n')) throw new Error(`skill frontmatter missing: ${file}`)
  const end = text.indexOf('\n---', 4)
  if (end === -1) throw new Error(`skill frontmatter unterminated: ${file}`)
  const fields = {}
  for (const line of text.slice(4, end).split('\n')) {
    if (!line || /^[ \t-]/.test(line)) continue
    const separator = line.indexOf(':')
    if (separator === -1) continue
    fields[line.slice(0, separator).trim()] = line
      .slice(separator + 1)
      .trim()
      .replace(/^["']|["']$/g, '')
  }
  return { fields, body: text.slice(end + 4).replace(/^\n/, '') }
}

/**
 * Rewrite the shim body so the plugin root is an absolute installed path.
 * The shims are written for a filesystem-discovered plugin directory, where the
 * root is `../../../..` from the skill file; a runtime registration has no such
 * anchor, so the root is stated explicitly instead of inferred.
 * @param {string} command - public command the shim projects.
 * @param {string} body - shim body without frontmatter.
 * @returns {string} model-facing skill body.
 */
function renderContent(command, body) {
  const resolved = body.replace(
    /插件根为当前文件的\s*`[^`]*`。/,
    `插件根为 \`${PACKAGE_ROOT}\`。`,
  )
  return [
    `Plugin root: \`${PACKAGE_ROOT}\``,
    `Canonical command contract: \`${join(PACKAGE_ROOT, 'commands', `${command}.md`)}\``,
    `Host manifest: \`${join(PACKAGE_ROOT, 'hosts', 'deepseek-dsh', 'host.json')}\``,
    '',
    resolved,
  ].join('\n')
}

/**
 * Collect every shim in the shipped host kit, failing loudly on an incomplete set.
 * @returns {{ name: string, description: string, content: string, command: string }[]}
 *   one entry per public command, ordered by command.
 */
function collectSkills() {
  const seen = new Map()
  for (const entry of readdirSync(SKILLS_ROOT).sort()) {
    const directory = join(SKILLS_ROOT, entry)
    if (!statSync(directory).isDirectory()) continue
    const { fields, body } = parseSkillFile(join(directory, 'SKILL.md'))
    const skillName = fields.name ?? ''
    if (!skillName.startsWith(SKILL_PREFIX)) {
      throw new Error(`skill name must start with "${SKILL_PREFIX}": ${entry}`)
    }
    if (!fields.description) throw new Error(`skill description missing: ${entry}`)
    const command = skillName.slice(SKILL_PREFIX.length)
    if (seen.has(skillName)) throw new Error(`duplicate skill name: ${skillName}`)
    seen.set(skillName, {
      name: skillName,
      description: fields.description,
      content: renderContent(command, body),
      command,
    })
  }
  const missing = COMMANDS.filter((command) => !seen.has(`${SKILL_PREFIX}${command}`))
  if (missing.length > 0) {
    throw new Error(`skill shims missing for: ${missing.join(', ')}`)
  }
  return COMMANDS.map((command) => seen.get(`${SKILL_PREFIX}${command}`))
}

/**
 * Register every AegisHarness skill with the profile's skill registry.
 * @param {import('@deepseek-ai/cordis').Context} ctx - composition context.
 * @returns {void}
 */
function apply(ctx) {
  for (const skill of collectSkills()) {
    ctx.skills.register({
      name: skill.name,
      description: skill.description,
      content: skill.content,
      source: 'bundled',
      provider: name,
      resourceBase: { kind: 'directory', path: PACKAGE_ROOT },
      invocation: { modelInvocable: true, userInvocable: true },
    })
  }
}

export { collectSkills, apply, inject, name }
