const menuIcon = document.getElementsByClassName('menu-icon');


for (el of menuIcon) {
    el.addEventListener('click', handler);
}

function handler(e) {
    const target=e.target;

    const menu=e.target.nextElementSibling;

    if (menu != null)
        menu.classList.toggle('visible');

    window.addEventListener('click', function(e) {
        if (e.target == target) return;

        if (menu.classList.contains('visible')) {
            menu.classList.remove('visible');
        }
    })
}

const likeBtn = document.getElementsByClassName('like');

for (el of likeBtn) {
    el.addEventListener('click', function handler(e) {
        e.preventDefault();
        const icon=this.firstElementChild;
        const count=this.querySelector('.like-count');

        icon.classList.toggle('fill');
        if (icon.classList.contains('fill')) {
            count.textContent=parseInt(count.textContent)+1;
        } else {
            count.textContent=parseInt(count.textContent)-1;
        }
        // console.log(this.getAttribute('href'));
        fetch(this.getAttribute('href')).then(res=>res.json()).then(res=>console.log(res));
    })
}

// For profile image
const profileImg = document.getElementById('dp');
window.addEventListener('load', function handler(e) {
    const wd=profileImg.naturalWidth; 
    const ht=profileImg.naturalHeight;

    if (wd <= ht) {
      profileImg.style.height=null;
      profileImg.style.width='100%';
    }
    else {
      profileImg.style.width=null;
      profileImg.style.height='100%';
    }
})
