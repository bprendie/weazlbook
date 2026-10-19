let menuVisible=true;
let state,tab='library',focusIndex=0,busy=false;
const $=s=>document.querySelector(s);
const status=text=>$('#status').textContent=text;
function refresh(data){state=data;$('#title').textContent=state.title;$('#page-label').textContent=`PAGE ${state.page} / ${state.pages}`;$('#progress').textContent=`${state.progress}%${state.read?' · READ':''}`;$('#progress-bar').style.width=state.progress+'%';$('#source').textContent=state.source;$('#font').value=state.size;$('#mark-count').textContent=state.bookmarks.length;$('#page-number').max=state.pages;$('#page-number').value=state.page;if(!state.security?.locked)$('#screen').src='/screen.png?v='+state.revision;$('#screen').alt=`${state.title}, page ${state.page} of ${state.pages}, rendered in IBM Plex Mono`;$('#notes').textContent=state.warnings.join(' · ')||'Reflowable local book. No import warnings.';$('#read-toggle').textContent=state.read?'MARK AS UNREAD':'MARK AS READ';window.syncSecurity?.();renderList()}
function renderList(){const list=$('#list');list.replaceChildren();let items=menuItems();focusIndex=Math.max(0,Math.min(focusIndex,items.length-1));if(!items.length){const p=document.createElement('p');p.className='empty';p.textContent=tab==='bookmarks'?'No marks yet. Press MARK to save this place.':'Nothing here yet.';list.append(p)}items.forEach((item,i)=>{const row=document.createElement('div');row.className='item';const button=document.createElement('button');button.className=i===focusIndex?'focused':'';button.textContent=item.label||item.name||item.title+` · ${item.progress}%${item.read?' · READ':''}`;button.onclick=()=>{focusIndex=i;activate(i)};row.append(button);if(tab==='bookmarks'){const del=document.createElement('button');del.className='remove';del.textContent='×';del.setAttribute('aria-label','Delete bookmark '+item.name);del.onclick=()=>action('delete_mark',{index:i},'Bookmark removed.');row.append(del)}list.append(row)});renderDeviceMenu()}
async function action(actionName,params={},message='Position saved locally.'){if(busy)return;busy=true;try{const response=await fetch('/api/action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:actionName,...params})});const data=await response.json();if(!response.ok)throw Error(data.error);refresh(data);status(message)}catch(e){status(e.message)}finally{busy=false}}
function menuItems(){if(!state)return [];if(tab==='settings')return [{label:'Unlock code',setting:'unlock'},{label:'Nuke Code',setting:'duress'}];if(tab==='contents')return state.toc;if(tab==='bookmarks')return state.bookmarks;return [...state.library,{label:'Settings',setting:'settings'},{label:'file_id.diz',setting:'about'}]}
function activate(i){const item=menuItems()[i];if(!item)return;if(item.setting){if(item.setting==='settings')setTab('settings');else if(item.setting==='about'){action('about',{},'Owner information.');menuVisible=false;renderDeviceMenu()}else configureLock(false,item.setting);return}if(tab==='contents')action('contents',{target:item.target});else if(tab==='bookmarks')action('jump_mark',{index:i});else action('open',{book:item.id},'Book opened.');menuVisible=false;renderDeviceMenu()}
function setTab(name){menuVisible=true;tab=name;focusIndex=0;document.querySelectorAll('[data-tab]').forEach(b=>b.classList.toggle('active',b.dataset.tab===tab));renderList()}
function mark(){if(!state?.pages)return;$('#mark-name').value=`${state.title} · page ${state.page}`;$('#mark-dialog').showModal();$('#mark-name').select()}
document.querySelectorAll('[data-action]').forEach(b=>b.onclick=()=>action(b.dataset.action));document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>setTab(b.dataset.tab));$('#back').onclick=backMenu;$('#mark').onclick=mark;$('#font').onchange=e=>action('font',{size:Number(e.target.value)},'Text size changed. Your place is preserved.');$('#goto').onsubmit=e=>{e.preventDefault();action('goto',{page:Number($('#page-number').value)})};$('#mark-form').onsubmit=e=>{if(e.submitter?.value==='save'){e.preventDefault();action('mark',{name:$('#mark-name').value},'Bookmark saved.');$('#mark-dialog').close();setTab('bookmarks')}};
function nav(direction){if(direction==='select'){activate(focusIndex);return}focusIndex+=direction==='up'?-1:1;renderList();$('#list .focused')?.scrollIntoView({block:'nearest'})}
document.querySelectorAll('[data-nav]').forEach(b=>b.onclick=()=>nav(b.dataset.nav));document.addEventListener('keydown',e=>{if(window.deviceLocked||$('#lock-dialog').open||$('#mark-dialog').open||['INPUT','SELECT','TEXTAREA'].includes(e.target.tagName)||e.ctrlKey||e.metaKey||e.altKey)return;if(e.repeat)return;const map={ArrowLeft:()=>action('previous'),ArrowRight:()=>action('next'),ArrowUp:()=>nav('up'),ArrowDown:()=>nav('down'),Enter:()=>nav('select')};if(map[e.key]){e.preventDefault();map[e.key]()}});
$('#export').onclick=async()=>{const r=await fetch('/api/export'),data=await r.json();const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='weazlbook-state-v1.json';a.click();URL.revokeObjectURL(url);status('Reading state exported.')};$('#import').onchange=async e=>{try{const f=e.target.files[0];if(!f)return;if(f.size>2*1024*1024)throw Error('Import limit is 2 MiB');await action('import_state',{state:JSON.parse(await f.text())},'Bookmarks merged; existing local progress preserved.')}catch(error){status(error.message)}};
fetch('/api/state').then(r=>r.json()).then(s=>{refresh(s);status(window.deviceLocked?'Locked. Enter your arrow sequence.':'Ready. Your book stays on this computer.')}).catch(e=>status(e.message));

let sleeping=false,idleTimer;
function scheduleSleep(){clearTimeout(idleTimer);if(!sleeping)idleTimer=setTimeout(()=>setSleeping(true),5*60*1000)}
function setSleeping(value){sleeping=value;$('#screensaver').hidden=!value;$('#sleep-toggle').setAttribute('aria-pressed',String(value));$('#sleep-toggle').textContent=value?'WAKE READER':'SCREENSAVER';status(value?'Sleeping. Press any key or tap the screen to resume.':'Ready. Your reading position is preserved.');scheduleSleep()}
$('#sleep-toggle').onclick=()=>setSleeping(!sleeping);
$('#screensaver').onclick=()=>setSleeping(false);
// Consume the first control press on wake so it cannot turn a page or create a mark.
for(const eventName of ['click','keydown'])document.addEventListener(eventName,e=>{
 if(e.target.closest('#reset-simulator')||window.deviceLocked||$('#lock-dialog').open)return;
 if(sleeping&&!(eventName==='click'&&e.target.closest('#sleep-toggle'))){if(eventName==='keydown'&&(e.ctrlKey||e.metaKey||e.altKey||e.key==='Tab'))return;e.preventDefault();e.stopImmediatePropagation();setSleeping(false);return}
 scheduleSleep();
},true);
for(const eventName of ['pointermove','touchstart','input','scroll'])document.addEventListener(eventName,scheduleSleep,{passive:true});
scheduleSleep();

function backMenu(){if(menuVisible&&tab!=='library')setTab('library');else if(menuVisible&&state.pages){menuVisible=false;renderDeviceMenu()}else setTab('library')}
function renderDeviceMenu(){
 $('#device-menu').hidden=!menuVisible;
 const list=$('#device-menu-list');list.replaceChildren();
 $('#device-menu .menu-heading').textContent=tab==='library'?'MAIN MENU':tab==='settings'?'SETTINGS':tab==='bookmarks'?'YOUR MARKS':'CONTENTS';
 if(!state)return;
 const items=menuItems();
 if(!items.length){list.textContent='Nothing here yet.';return}
 items.forEach((item,i)=>{const b=document.createElement('button');b.className=i===focusIndex?'focused':'';b.textContent=item.label||item.name||item.title;
 if(tab==='library'&&!item.setting){const small=document.createElement('small');small.textContent=`${item.progress}% COMPLETE${item.read?' · READ':''}`;b.append(small)}
 b.onclick=()=>{focusIndex=i;activate(i)};list.append(b)});
 list.querySelector('.focused')?.scrollIntoView({block:'nearest'});
}
$('#read-toggle').onclick=()=>action('read_status',{read:!state.read},state.read?'Marked unread.':'Marked read.');

$('#settings-button').onclick=()=>setTab('settings');
$('#about-button').onclick=()=>{action('about',{},'Owner information.');menuVisible=false;renderDeviceMenu()};
$('#reset-simulator').onclick=async()=>{await securityCall('reset_simulator');menuVisible=true;setTab('library');status('Simulator reset. Original files preserved.')};
