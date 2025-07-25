let toggler = document.getElementById("toggle");
let div = document.getElementById("div");
let exit_button = document.getElementById("exit-btn")

toggler.addEventListener("click", toggle)
exit_button.addEventListener("click",exit)

function toggle(){
    div.style.display = "block"
}
function exit(){
    div.style.display = "none"
}
