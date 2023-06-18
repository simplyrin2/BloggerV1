const deleteBtn = document.querySelector('.delete-action');
const deleteConfirm = document.querySelector('.delete-confirmation');
const overlay = document.querySelector('.overlay-back');
const cancelBtn = document.querySelector('.deny');

function closeConfirmation(e) {
    deleteConfirm.style.transform = 'scale(0)';
}

deleteBtn.addEventListener('click', function handler(e){
    deleteConfirm.style.transform = 'scale(1)';
})

overlay.addEventListener('click', closeConfirmation);
cancelBtn.addEventListener('click', closeConfirmation);
