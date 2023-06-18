const backbtn = document.getElementById('back-button');

backbtn?.addEventListener('click', function handler(e) {
    e.preventDefault();
    window.history.back();
})

const badge = document.querySelector('.badge');

function badge_handler(e) {
    if (!badge.classList.contains('visible')) {
        this.fetch('/n-badge').then(res=>res.json()).then((res)=>{
            console.log(res.count);
            if (res.count > 0){
                badge.classList.add('visible');
            }
        })
    }
}

window.addEventListener('load', badge_handler)
setInterval(badge_handler, 5000);

