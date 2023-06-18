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
        console.log(this.getAttribute('href'));
        fetch(this.getAttribute('href')).then(res=>res.json()).then(res=>console.log(res));
    })
}
