"""Disposable simulator test: never uses live state or deletes source documents."""
import subprocess, tempfile, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as temp:
 proc=subprocess.Popen(['.venv/bin/python','-m','reader.web','--book','fixtures/formatting.md','--state',temp,'--port','5001'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  for _ in range(100):
   try:urllib.request.urlopen('http://localhost:5001/api/state');break
   except OSError:time.sleep(.05)
  with sync_playwright() as p:
   browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium');page=browser.new_page(viewport={'width':1400,'height':1100});errors=[]
   page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto('http://localhost:5001');page.wait_for_function("typeof state !== 'undefined'")
   assert page.locator('#device-menu').is_visible()
   page.locator('#settings-button').click()
   def setcode(label,keys):
    page.locator('#device-menu-list button').filter(has_text=label).click()
    for key in keys:page.keyboard.press(key)
    page.locator('#sequence-next').click()
    for key in keys:page.keyboard.press(key)
    page.locator('#sequence-next').click();page.wait_for_function("!document.querySelector('#lock-dialog').open")
   unlock=['ArrowUp','ArrowUp','ArrowDown','ArrowDown','ArrowLeft','ArrowRight','ArrowLeft','ArrowRight']
   duress=['ArrowDown','ArrowDown','ArrowUp','ArrowUp','ArrowRight','ArrowLeft','ArrowRight','ArrowLeft']
   setcode('Unlock code',unlock);setcode('Nuke Code',duress)
   page.locator('#about-button').click();page.wait_for_function("state.title.includes('file_id.diz')")
   page.keyboard.down('Escape');page.keyboard.down('m');page.keyboard.up('m');page.keyboard.up('Escape')
   page.wait_for_function('window.deviceLocked')
   assert page.request.get('http://localhost:5001/api/export').status==403
   assert page.request.get('http://localhost:5001/screen.png').status==403
   page.reload();page.wait_for_function('window.deviceLocked')
   for key in duress:page.keyboard.press(key)
   page.wait_for_function('state.security.purged')
   assert not page.locator('#lock-dialog').is_visible()
   assert not page.evaluate('state.security.unlock_set || state.security.duress_set')
   page.locator('#reset-simulator').click();page.wait_for_function('state.library.length===1')
   assert not page.evaluate('state.security.unlock_set || state.security.duress_set')
   page.locator('#device-menu-list button').filter(has_text='A pocket library').click()
   page.keyboard.down('m');page.wait_for_timeout(650);page.keyboard.up('m')
   assert page.locator('#device-menu .menu-heading').inner_text()=='YOUR MARKS'
   assert not page.locator('#mark-dialog').is_visible()
   page.keyboard.press('Escape');page.keyboard.press('Escape')
   page.locator('#read-toggle').click();page.wait_for_function('state.read')
   page.locator('[data-tab="library"]').click()
   assert 'READ' in page.locator('#device-menu-list').inner_text()
   page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
   page.screenshot(path='artifacts/simulator-main-menu-mobile.png',full_page=True)
   assert not errors,errors
   browser.close();print('PASS: menu, settings, codes, About, lock API enforcement, reload, immediate duress, safe reset, hold MARK, READ, mobile')
 finally:
  proc.terminate();proc.wait(timeout=10)
