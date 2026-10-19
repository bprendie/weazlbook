from playwright.sync_api import sync_playwright
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium');page=b.new_page();errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://localhost:5000');page.wait_for_function("typeof state!=='undefined'")
 initial=page.locator('#page-label').inner_text()
 page.keyboard.down('Escape');page.keyboard.down('m');page.keyboard.up('m');page.keyboard.up('Escape')
 assert page.locator('#lock-dialog').is_visible()
 combo=['ArrowUp','ArrowUp','ArrowDown','ArrowDown','ArrowLeft','ArrowRight','ArrowLeft','ArrowRight']
 for key in combo:page.keyboard.press(key)
 page.locator('#sequence-next').click()
 for key in ['ArrowDown']*4:page.keyboard.press(key)
 page.locator('#sequence-next').click();assert 'did not match' in page.locator('#sequence-prompt').inner_text()
 for key in combo:page.keyboard.press(key)
 page.locator('#sequence-next').click();assert page.evaluate('window.deviceLocked')
 page.reload();page.wait_for_function("typeof state!=='undefined'");assert page.evaluate('window.deviceLocked')
 page.locator('#screensaver').click();page.keyboard.press('Enter');assert page.evaluate('window.deviceLocked')
 for key in ['ArrowRight']*8:page.keyboard.press(key)
 assert page.evaluate('window.deviceLocked')
 assert page.locator('#page-label').inner_text()==initial
 for key in combo:page.keyboard.press(key)
 assert not page.evaluate('window.deviceLocked')
 assert page.locator('#page-label').inner_text()==initial
 # Mouse hold BACK + keyboard M emulates the two-button chord with one pointer.
 page.locator('#back').hover();page.mouse.down();page.keyboard.down('m');page.keyboard.up('m');page.mouse.up()
 assert page.evaluate('window.deviceLocked')
 for selector in ['.nav .up','.nav .up','.nav .down','.nav .down','.nav .left','.nav .right','.nav .left','.nav .right']:page.locator(selector).click()
 assert not page.evaluate('window.deviceLocked')
 assert not page.locator('#mark-dialog').is_visible()
 assert page.locator('#page-label').inner_text()==initial
 page.keyboard.press('m');assert page.locator('#mark-dialog').is_visible();page.keyboard.press('Escape')
 assert not errors,errors
 print('PASS setup, confirmation mismatch, chord, persisted lock, wrong sequence, blocked wake, keyboard and pointer unlock, preserved page, standalone MARK')
 b.close()
