const fileInput=document.getElementById('fileInput');
const imgInputBtn = document.querySelector('.img-input');
const imgPreview = document.getElementById('img-preview');
const imgPlaceHolder = document.querySelector('.imgInput-placeholder');
const cancel = document.querySelector('#cancel');


imgInputBtn.addEventListener('click', function handler(e) {
    fileInput.click();
})


fileInput.addEventListener('change', function handler(e) {
    file=e.target.files[0];

    if (!file) return;
    if (!file.type.startsWith('image/')) return;

    const fileReader = new FileReader();
    fileReader.addEventListener('load', (e) => {
      imgPreview.src = e.target.result;

      imgPreview.addEventListener('load', function handler(e) {
        const wd=imgPreview.naturalWidth; 
        const ht=imgPreview.naturalHeight;

        if (wd <= ht) {
          imgPreview.style.height=null;
          imgPreview.style.width='100%';
        }
        else {
          imgPreview.style.width=null;
          imgPreview.style.height='100%';
        }
      })
      
      imgPlaceHolder.style.display='none';
      cancel.style.display='block';
    });
    fileReader.readAsDataURL(file);    
})

cancel.addEventListener('click', function handler(e) {
    if (!fileInput.value) return;

    fileInput.value=null;
    imgPreview.src='';
    imgPlaceHolder.style.display='flex';
    cancel.style.display='none';
})

const uploadInput = document.getElementById('fileInput');
uploadInput.addEventListener('change', function(e) {
    console.log('EH');
    console.log(this.files[0].size);
    document.cookie="size="+this.files[0].size;
})
