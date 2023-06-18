const img_container = document.querySelector('.post-image');
const img = document.querySelector('.image');
const overlay = document.querySelector('.overlay-back')

img?.addEventListener('click', function handler(e) {
    img_container.classList.toggle('overlay');
})

overlay?.addEventListener('click', function handler(e) {
    img_container.classList.remove('overlay');
})

// Like Button
const likeBtn = document.getElementsByClassName('like');
const likeCount = document.querySelector('.like-count').firstElementChild;

for (el of likeBtn) {
    el.addEventListener('click', function handler(e) {
        e.preventDefault();
        const icon=this.firstElementChild;

        icon.classList.toggle('fill');
        if (icon.classList.contains('fill')) {
            likeCount.textContent=parseInt(likeCount.textContent.split(' ')[0])+1+" Likes";
        } else {
            likeCount.textContent=parseInt(likeCount.textContent.split(' ')[0])-1+" Likes";
        }
        fetch(this.getAttribute('href')).then(res=>res.json()).then(res=>console.log(res));
    })
}

