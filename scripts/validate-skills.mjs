#!/usr/bin/env node
import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const skillsRoot = path.join(root, 'skills')
const skillDirectories = fs.readdirSync(skillsRoot, { withFileTypes: true })
  .filter(entry => entry.isDirectory())
  .map(entry => entry.name)
  .sort()

assert.deepEqual(skillDirectories, ['ziwei'])

let checkedLinks = 0

function readJson(relativePath) {
  return JSON.parse(fs.readFileSync(path.join(root, relativePath), 'utf8'))
}

function markdownFiles(directory) {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap(entry => {
    const absolute = path.join(directory, entry.name)
    if (entry.isDirectory()) return markdownFiles(absolute)
    return entry.isFile() && entry.name.endsWith('.md') ? [absolute] : []
  })
}

for (const directoryName of skillDirectories) {
  const skillFile = path.join(skillsRoot, directoryName, 'SKILL.md')
  const skill = fs.readFileSync(skillFile, 'utf8')
  const frontmatter = skill.match(/^---\n([\s\S]*?)\n---\n/)
  assert(frontmatter, `${directoryName}: 缺少 YAML frontmatter`)
  assert.match(frontmatter[1], new RegExp(`^name: ${directoryName}$`, 'm'))
  assert.match(frontmatter[1], /^description: .+$/m)
  assert.match(directoryName, /^[a-z0-9]+(?:-[a-z0-9]+)*$/)

  for (const markdownFile of markdownFiles(path.join(skillsRoot, directoryName))) {
    const contents = fs.readFileSync(markdownFile, 'utf8')
    if (path.basename(markdownFile).startsWith('_draft-')) continue
    for (const match of contents.matchAll(/\[[^\]]*\]\(([^)]+)\)/g)) {
      const target = match[1]
      if (/^(?:https?:|mailto:|#)/.test(target)) continue
      const decoded = decodeURIComponent(target.split('#')[0])
      assert(fs.existsSync(path.resolve(path.dirname(markdownFile), decoded)),
        `${path.relative(root, markdownFile)}: 无效链接 ${target}`)
      checkedLinks += 1
    }
  }
}

const forbidden = /令东来|王亭之|陆斌兆|紫云先生|骨髓赋|紫微斗数全书|紫微斗数命理学|中州学派|PDF.?掃描/
for (const markdownFile of markdownFiles(path.join(skillsRoot, 'ziwei'))) {
  if (path.basename(markdownFile).startsWith('_draft-')) continue
  const contents = fs.readFileSync(markdownFile, 'utf8')
  const hit = contents.match(forbidden)
  assert(!hit, `${path.relative(root, markdownFile)}: 来源痕迹 ${hit && hit[0]}`)
}

const suiteFile = path.join(root, 'workbuddy/ziwei-skills/SKILL.md')
assert(fs.existsSync(suiteFile), '缺少 workbuddy/ziwei-skills/SKILL.md')

const codexPlugin = readJson('.codex-plugin/plugin.json')
assert.equal(codexPlugin.name, 'ziwei-skills')
assert.match(codexPlugin.version, /^\d+\.\d+\.\d+$/)
assert.equal(codexPlugin.license, 'MIT')
assert.equal(codexPlugin.skills, './skills/')
assert.equal(codexPlugin.author.name, 'songgoldenwind-crypto')
assert(Array.isArray(codexPlugin.interface.defaultPrompt))
assert(codexPlugin.interface.defaultPrompt.length <= 3)

const claudePlugin = readJson('.claude-plugin/plugin.json')
assert.equal(claudePlugin.name, codexPlugin.name)
assert.equal(claudePlugin.version, codexPlugin.version)
assert.equal(claudePlugin.license, 'MIT')

const claudeMarketplace = readJson('.claude-plugin/marketplace.json')
assert.equal(claudeMarketplace.plugins.length, 1)
assert.equal(claudeMarketplace.plugins[0].name, codexPlugin.name)
assert.equal(claudeMarketplace.plugins[0].source, './')
assert.equal(claudeMarketplace.plugins[0].version, codexPlugin.version)

const codexMarketplace = readJson('.agents/plugins/marketplace.json')
assert.equal(codexMarketplace.plugins.length, 1)
assert.equal(codexMarketplace.plugins[0].name, codexPlugin.name)
assert.equal(codexMarketplace.plugins[0].source.source, 'url')
assert.equal(codexMarketplace.plugins[0].source.url,
  'https://github.com/songgoldenwind-crypto/ziwei-skills.git')
assert.equal(codexMarketplace.plugins[0].source.ref, 'master')

assert(fs.existsSync(path.join(root, 'skills/ziwei/scripts/run_paipan.py')),
  '缺少统一排盘入口 scripts/run_paipan.py')

const license = fs.readFileSync(path.join(root, 'LICENSE'), 'utf8')
assert.match(license, /^MIT License\n/)
assert.match(license, /Copyright \(c\) 2026 songgoldenwind-crypto/)

const workbuddyAdapter = fs.readFileSync(path.join(root, 'scripts/workbuddy_compat.py'), 'utf8')
for (const skill of ['ziwei-skills', ...skillDirectories]) {
  assert.match(workbuddyAdapter, new RegExp(`^[ ]{4}"${skill}": \\{$`, 'm'))
}

console.log(JSON.stringify({
  status: 'pass',
  skills: skillDirectories.length,
  checkedLinks,
  manifests: 4,
}))
