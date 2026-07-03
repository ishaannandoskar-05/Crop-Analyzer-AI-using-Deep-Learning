let home = document.getElementById("home");
let about = document.getElementById("about");

// Only keep the style changes for the buttons
home.addEventListener("click", function() {
    home.style.backgroundColor = "#446d2c";
    about.style.backgroundColor = "#395b25";
});

about.addEventListener("click", function() {
    about.style.backgroundColor = "#446d2c";
    home.style.backgroundColor = "#395b25";
});

// Image preview handling
document.getElementById("input")?.addEventListener("change", function(event) {
    let file = event.target.files[0];
    let preview = document.getElementById("preview");

    if (file) {
        let imagePath = URL.createObjectURL(file);
        preview.src = imagePath;
        preview.style.display = "block";
        footer.style.position = "relative";
        this.blur();
    } else {
        preview.style.display = "none";
        preview.src = "";
    }
});

// Reset image on page refresh
window.onload = function() {
    let preview = document.getElementById("preview");
    if (preview) {
        preview.style.display = "none";
        preview.src = "";
    }
};

let footer = document.getElementById("footerr");

