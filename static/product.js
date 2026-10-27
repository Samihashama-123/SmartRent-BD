/* Accessibility and interaction utilities. This file does not change user data. */
(()=>{'use strict';
  document.addEventListener('click',event=>{
    const menu=document.querySelector('.sr-menu[open]');
    if(menu&&!menu.contains(event.target))menu.removeAttribute('open');
    if(event.target instanceof Element&&event.target.matches('.sr-mobile-menu a')){
      const nav=document.querySelector('.sr-mobile-menu');
      nav?.setAttribute('hidden','');
    }
  });
  document.addEventListener('keydown',event=>{
    if(event.key==='Escape'){
      document.querySelectorAll('.sr-menu[open]').forEach(el=>el.removeAttribute('open'));
      const mobile=document.getElementById('sr-mobile-menu');
      if(mobile&&!mobile.hasAttribute('hidden')){
        mobile.setAttribute('hidden','');
        const button=document.querySelector('.sr-mobile-toggle');
        button?.setAttribute('aria-expanded','false');
      }
    }
  });
})();
