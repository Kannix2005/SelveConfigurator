import{c as l,j as o,d as s,h,g,k as p,J as d}from"./index.bf3c9ec7.js";import{h as y}from"./render.172e8b84.js";var v=l({name:"QPage",props:{padding:Boolean,styleFn:Function},setup(a,{slots:r}){const{proxy:{$q:n}}=g(),e=o(p);o(d,()=>{console.error("QPage needs to be child of QPageContainer")});const i=s(()=>{const t=(e.header.space===!0?e.header.size:0)+(e.footer.space===!0?e.footer.size:0);if(typeof a.styleFn=="function"){const u=e.isContainer.value===!0?e.containerHeight.value:n.screen.height;return a.styleFn(t,u)}return{minHeight:e.isContainer.value===!0?e.containerHeight.value-t+"px":n.screen.height===0?t!==0?`calc(100vh - ${t}px)`:"100vh":n.screen.height-t+"px"}}),c=s(()=>`q-page ${a.padding===!0?" q-layout-padding":""}`);return()=>h("main",{class:c.value,style:i.value},y(r.default))}});export{v as Q};
