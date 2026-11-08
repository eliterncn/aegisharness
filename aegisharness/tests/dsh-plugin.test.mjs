/**
 * Offline smoke test for the dsh bundle entry.
 *
 * Runs with plain Node and no dsh installation: it asserts that the module the
 * profile will mount registers exactly the nine public commands, with bodies that
 * point at absolute paths inside the installed package. Run with:
 *
 *     node tests/dsh-plugin.test.mjs
 */
import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

import { apply, collectSkills, inject, name } from '../lib/index.js'

const PACKAGE_ROOT = dirname(dirname(fileURLToPath(import.meta.url)))
const COMMANDS = ['init', 'propose', 'apply', 'archive', 'bug-fix', 'ut', 'update', 'status', 'config']
const KEBAB = /^[a-z0-9]+(?:-[a-z0-9]+)*$/

assert.equal(name, 'aegisharness')
assert.deepEqual(inject, ['skills'])

const skills = collectSkills()
assert.equal(skills.length, COMMANDS.length, 'one skill per public command')
assert.deepEqual(skills.map((skill) => skill.command), COMMANDS)

for (const skill of skills) {
  assert.match(skill.name, KEBAB, `kebab-case skill name: ${skill.name}`)
  assert.equal(skill.name, `aegis-${skill.command}`)
  assert.ok(skill.description.length > 0, `description present: ${skill.name}`)
  assert.ok(skill.content.includes(`Plugin root: \`${PACKAGE_ROOT}\``), `absolute root in ${skill.name}`)
  const contract = join(PACKAGE_ROOT, 'commands', `${skill.command}.md`)
  assert.ok(existsSync(contract), `canonical contract exists: ${contract}`)
  assert.ok(skill.content.includes(contract), `contract path in ${skill.name}`)
  assert.ok(!skill.content.includes('当前文件的 `../../'), `relative root rewritten in ${skill.name}`)
}

const registered = []
apply({ skills: { register: (skill) => registered.push(skill) } })
assert.equal(registered.length, COMMANDS.length, 'apply registers every skill')
for (const skill of registered) {
  assert.equal(skill.provider, 'aegisharness')
  assert.equal(skill.source, 'bundled')
  assert.deepEqual(skill.invocation, { modelInvocable: true, userInvocable: true })
  assert.equal(skill.resourceBase.kind, 'directory')
  assert.equal(skill.resourceBase.path, PACKAGE_ROOT)
}

// The bundle layer and the module must agree, or the profile mounts a name that
// resolves to a different entry than the one this test exercised.
const manifest = JSON.parse(readFileSync(join(PACKAGE_ROOT, 'package.json'), 'utf8'))
assert.equal(manifest.dsh?.bundle?.patch, './cordis.patch.yml')
const patch = readFileSync(join(PACKAGE_ROOT, 'cordis.patch.yml'), 'utf8')
assert.ok(patch.includes(manifest.name), `patch inserts ${manifest.name}`)
assert.ok(patch.includes('id: aegisharness'))

process.stdout.write(`dsh plugin smoke test OK: ${skills.length} skills\n`)
