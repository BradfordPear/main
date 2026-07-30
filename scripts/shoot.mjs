import { chromium } from 'playwright-core'

const EXE = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
const BASE = process.env.URL || 'http://localhost:4173/main/'
const OUT = '/tmp/claude-0/-home-user-main/7b9d511f-50a4-538f-bf55-eee8f32f3f1f/scratchpad'

const browser = await chromium.launch({ executablePath: EXE, args: ['--no-sandbox'] })
const page = await browser.newPage({ viewport: { width: 412, height: 900 } })
const errors = []
page.on('console', (m) => m.type() === 'error' && errors.push(m.text()))
page.on('pageerror', (e) => errors.push('PAGEERROR: ' + e.message))

async function shot(name) {
  await page.screenshot({ path: `${OUT}/shot-${name}.png` })
  console.log('shot', name)
}

await page.goto(BASE, { waitUntil: 'networkidle' })
await page.waitForTimeout(400)
await shot('01-setup')

// Pick the Test Deck category (visible when SHOW_TEST is on).
await page.getByText('Test Deck', { exact: false }).first().click()
// Fill two player names.
const inputs = page.locator('input.input')
await inputs.nth(0).fill('Liam')
await inputs.nth(1).fill('Priya')
await page.waitForTimeout(200)
await shot('02-setup-filled')

// Start.
await page.getByRole('button', { name: /Take the throne/ }).click()
await page.waitForTimeout(600)
await shot('03-reveal')

// Object.
await page.getByRole('button', { name: 'OBJECTION!' }).click()
await page.waitForTimeout(300)
await shot('04-objection')
// Pick advocate.
await page.getByRole('button', { name: 'Liam' }).first().click()
await page.waitForTimeout(300)
await shot('05-defender')
// Room defends.
await page.getByRole('button', { name: /room defends/ }).click()
await page.waitForTimeout(400)
await shot('06-debate')
// Skip to vote.
await page.getByRole('button', { name: /Skip to vote/ }).click()
await page.waitForTimeout(300)
await shot('07-vote')
// Both vote challenger to force a dethrone.
const chall = page.getByRole('button', { name: /votes challenger/ })
await chall.nth(0).click()
await chall.nth(1).click()
await page.waitForTimeout(200)
await shot('08-vote-filled')
await page.getByRole('button', { name: /Reveal the verdict/ }).click()
await page.waitForTimeout(700)
await shot('09-result')

await browser.close()
console.log('CONSOLE ERRORS:', errors.length ? JSON.stringify(errors, null, 2) : 'none')
