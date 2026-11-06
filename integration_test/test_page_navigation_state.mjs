import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const requests = [];
const noUpdate = {};
let counter = 0;
const window = {crypto:{randomUUID:()=>String(++counter)}, dash_clientside:{
    no_update:noUpdate, set_props:(id,props)=>requests.push({id,...props})
}};
vm.runInNewContext(readFileSync(new URL('../assets/page_navigation.js', import.meta.url),'utf8'), {window});
const nav = window.dash_clientside.page_navigation;
const component = props => ({namespace:'dash_html_components',type:'Div',props});
const templates = {loading:component({className:'page-loading-screen',children:component({className:'page-loading-spinner'})})};
const session = {user_id:'u1',role:'admin',organization_id:'org'};
nav.render('/engine-management','',session,templates);
const first = requests.at(-1).data.id;
nav.render('/user-management','',session,templates);
const second = requests.at(-1).data.id;
assert.notEqual(first,second);
assert.equal(nav.complete({id:first,layout:'old'},'/user-management','',session),noUpdate);
assert.equal(nav.complete({id:second,layout:'new'},'/user-management','',session),'new');
assert.equal(nav.complete({id:second,layout:'new'},'/user-management','?changed=1',session),noUpdate);
assert.equal(nav.complete({id:second,layout:'new'},'/user-management','',{...session,user_id:'other'}),noUpdate);
nav.render('/','',null,templates);
assert.equal(nav.complete({id:second,layout:'private'},'/','',null),noUpdate);
console.log('PASS: stale routes, changed searches, switched accounts and logout reject obsolete responses');
