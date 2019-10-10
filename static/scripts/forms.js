(function () {

  // show progress bar on submit
  let submit_btn = document.querySelector('form');
  submit_btn.addEventListener('submit', showProgress);

})();

function showProgress() {
  let progressBar = document.getElementById('progress-bar');
  progressBar.classList.remove('hidden');
  return true;
}

function showPassword() {
  let icon = document.querySelector('.show-password i');
  let iconText = icon.innerText;

  // toggle visibility
  let input_type = (iconText == 'visibility') ? 'text' : 'password';
  let input = document.querySelectorAll('input#password, input#confirm_password');
  input.forEach(el => el.type = input_type);

  icon.classList.toggle('icon-pw-visible');

  // set boolean status
  if (input_type == 'text') {
    icon.innerText = 'visibility_off';
  } else {
    icon.innerText = 'visibility';
  }
}