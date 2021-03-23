const inputs = document.querySelectorAll('.input');
const flashNodes = document.querySelectorAll('.flash');
const species = document.querySelectorAll('.species');
const visibleChoose = document.querySelectorAll(".visible-checkbox");
const selected = document.querySelectorAll(".selected");
const areas = document.querySelectorAll("textarea");
const tabs = document.querySelectorAll(".tab");
const tabContents = document.querySelectorAll(".tab-content");

tabs.forEach(tab => {
    tab.addEventListener("click", () => {
       tabs.forEach(tab => {
          tab.classList.remove("focused");
       });
       tabContents.forEach(tabContent => {
          if(tabContent.classList.contains(tab.id))
            tabContent.classList.add("shown");
          else
            tabContent.classList.remove("shown");
       });
       tab.classList.toggle("focused");
    });
});

areas.forEach(area => {
    area.addEventListener('input', () => {
        area.parentNode.parentNode.style.height = "";
        area.parentNode.parentNode.style.height = area.scrollHeight + "px";
    });
    area.parentNode.parentNode.style.height = "";
    area.parentNode.parentNode.style.height = area.scrollHeight + "px";
});


visibleChoose.forEach(visible => {
    visible.addEventListener("click", () => {
        if(confirm('Wenn sie ihr Profil sichtbar machen, kann jeder ihren Benutzernamen und ihre E-Mail Adresse, sowie eine übersicht über ihre Aktivitäten auf dieser Internetseite sehen! Diese Aktion kann jederzeit rückgängig gemacht werden!')) {
            let parent = visible.parentNode.parentNode;
            open = parent.querySelector(".fa-eye");
            slash = parent.querySelector(".fa-eye-slash");
            label = parent.querySelector(".visible-text");



            if(visible.checked) {
                label.innerHTML = "Ihr Profil ist sichtbar";

                if(slash !== null) {
                    slash.classList.add("fa-eye");
                    slash.classList.remove("fa-eye-slash");
                }
                visible.checked = true;
            } else {
                label.innerHTML = "Ihr Profil ist unsichtbar";

                if(open !== null) {
                    open.classList.remove("fa-eye");
                    open.classList.add("fa-eye-slash");
                }
                visible.checked = false;
            }
        }
    });
});

selected.forEach(select => {
    arrow = select.parentNode.parentNode.parentNode.querySelector('.arrow');
    if(arrow !== null) {
        arrow.addEventListener("click", () => {
            optionContainer = select.parentNode.querySelector(".option-container");
            optionContainer.classList.toggle("active");
            arrowDown = select.parentNode.parentNode.parentNode.querySelector(".fa-angle-down");
            arrowUp = select.parentNode.parentNode.parentNode.querySelector(".fa-angle-up");
            if(arrowDown !== null) {
                arrowDown.classList.remove("fa-angle-down");
                arrowDown.classList.toggle("fa-angle-up");
            }

            if(arrowUp !== null) {
                arrowUp.classList.toggle("fa-angle-down");
                arrowUp.classList.remove("fa-angle-up");
            }
        });
    }

    select.addEventListener("click", () => {
        optionContainer = select.parentNode.querySelector(".option-container");
        optionContainer.classList.toggle("active");
        arrowDown = select.parentNode.parentNode.parentNode.querySelector(".fa-angle-down");
        arrowUp = select.parentNode.parentNode.parentNode.querySelector(".fa-angle-up");
        if(arrowDown !== null) {
            arrowDown.classList.remove("fa-angle-down");
            arrowDown.classList.toggle("fa-angle-up");
        }

        if(arrowUp !== null) {
            arrowUp.classList.toggle("fa-angle-down");
            arrowUp.classList.remove("fa-angle-up");
        }
    });

    if (!select.classList.contains('special')) {

        optionsList = select.parentNode.querySelectorAll(".option");
        optionsList.forEach( o => {
            o.addEventListener("click", () => {
                /*if(o.id !== "") {
                    location.href = '/home/' + o.id;
                }*/

                select.value = o.querySelector("label").innerHTML;
                optionContainer = select.parentNode.querySelector(".option-container");
                optionContainer.classList.remove("active");
                header = select.parentNode.parentNode.querySelector('.selection-header');
                if(header !== null) {
                    header.classList.add('active');
                }
                arrowUp = select.parentNode.parentNode.parentNode.querySelector(".fa-angle-up");
                if(arrowUp !== null) {
                    arrowUp.classList.toggle("fa-angle-down");
                    arrowUp.classList.remove("fa-angle-up");
                }
                if(select.id == 'area_select')
                    filterByArea()
            });
        });

    }
    searchBox = select.parentNode.querySelector(".search-box input");
    searchBox.addEventListener("keyup", function(e) {
        var input = e.target;
        var filter = input.value.toUpperCase();
        var options = select.parentNode.querySelectorAll('.option label');
        var i;
        for(i = 0; i < options.length; i++) {
            topic = options[i];

            if(topic.innerHTML.toUpperCase().indexOf(filter)>-1) {
                options[i].parentNode.style.display = "";
            } else {
                options[i].parentNode.style.display = "none";
            }
        }
    });


    let parent = select.parentNode.parentNode.parentNode;

    if(parent.querySelector('.second') == null && select.value !== null && select.value !== '') {
        parent.classList.add('focus');
    }
});

function focusFunc() {
    let parent = this.parentNode.parentNode;
    parent.classList.add('focus');
}

function blurFunc() {
    let parent = this.parentNode.parentNode;
    if(this.value == "") {
        parent.classList.remove('focus');
    }
}

inputs.forEach(input => {
    input.addEventListener('focus', focusFunc)
    input.addEventListener('blur', blurFunc)
    if(input.value != "") {
        let parent = input.parentNode.parentNode;
        parent.classList.add('focus');
    }
});

function onChangeViewSpecies() {
    element = document.getElementsByClassName(this.id)[0];
    element.addEventListener('animationend', speciesAnimationEnd);
    element.addEventListener("webkitAnimationEnd", speciesAnimationEnd);
    if(element.style.display == "none") {
        element.removeEventListener('animationend', speciesAnimationEnd);
        element.removeEventListener("webkitAnimationEnd", speciesAnimationEnd);
        element.style.display = "grid";
        e1 = this.querySelector(".fa-angle-down");
        if(e1 !== null) {
            e1.classList.toggle("fa-angle-up");
            e1.classList.remove("fa-angle-down");
        }
        element.style.animation = 'appear .5s ease-out 0s 1';
        e2 = element.querySelector(".card");
        e2.style.animation = 'appear-card .5s ease-out 0s 1';
    } else {
        e1 = this.querySelector(".fa-angle-up");
        if(e1 !== null) {
            e1.classList.toggle("fa-angle-down");
            e1.classList.remove("fa-angle-up");
        }
        element.style.animation = 'collapse .5s ease-out 0s 1';
        e2 = element.querySelector(".card");
        e2.style.animation = 'collapse-card .5s ease-out 0s 1';
    }
}

function speciesAnimationEnd() {
   element.style.display = "none";
}

species.forEach(input => {
    input.addEventListener('click', onChangeViewSpecies);
});

function clickFunc() {
    this.style.animation = 'fade-out .5s ease-out 0s 1';
}

function removeFlash() {
    this.style.display = 'none';
    this.style.animation = 'none';
}

flashNodes.forEach(flashNode => {
    flashNode.addEventListener('click', clickFunc);
    flashNode.addEventListener('animationend', removeFlash);
    flashNode.addEventListener("webkitAnimationEnd", removeFlash);
});

function triggerPictureChoose() {
    document.querySelector('#image_loader').click();
}

function displayImage(e) {
    if (e.files[0]) {
        var reader = new FileReader();

        reader.onload = function(e) {
            document.querySelector('#profile_picture').setAttribute('src', e.target.result);
        }

        reader.readAsDataURL(e.files[0]);
    }
}

function searchCharacters() {
    var input = document.getElementById("search");
    var filter = input.value.toUpperCase();
    var topics = document.getElementsByClassName('topic-section');
    var i;
    for(i = 0; i < topics.length; i++) {
        topic = topics[i];

        if(topic.className.toUpperCase().indexOf(filter) > -1) {
            topics[i].style.display = "";
        } else {
            topics[i].style.display = "none";
        }

    }

}

function add_filter() {
    var input1 = document.getElementById("search");
    var input2 = document.getElementById("select_tag");
    var tabContents = document.querySelectorAll(".searchable");

    var filter1 = input2.value.toUpperCase();
    var filter2 = input1.value.toUpperCase();

    var i;
    for(i = 0; i < tabContents.length; i++) {
        if(tabContents[i].className.toUpperCase().indexOf(filter1) > -1) {
            if(tabContents[i].innerText.toUpperCase().indexOf(filter2) > -1) {
                allNodes = tabContents[i].parentNode.querySelectorAll('td');
                var i1;
                for(i1 = 0; i1 < allNodes.length; i1++) {
                    allNodes[i1].style.display = "";
                }
            } else {
                allNodes = tabContents[i].parentNode.querySelectorAll('td');
                var i1;
                for(i1 = 0; i1 < allNodes.length; i1++) {
                    allNodes[i1].style.display = "none";
                }
            }
        }
    }
}

function filterByArea() {
    var input = document.getElementById("area_select");
    var tabContents = document.querySelectorAll(".searchable");
    var i;

    var filter1 = "Fläche".toUpperCase();
    var filter2 = input.value.toUpperCase();

    console.log('Param: ' + filter1);
    console.log('Search: ' + filter2);

    for(i = 0; i < tabContents.length; i++) {
        if(tabContents[i].className.toUpperCase().indexOf(filter1) > -1) {
            if(tabContents[i].innerText.toUpperCase().indexOf(filter2) > -1) {
                allNodes = tabContents[i].parentNode.querySelectorAll('td');
                var i1;
                for(i1 = 0; i1 < allNodes.length; i1++) {
                    allNodes[i1].style.display = "";
                }
            } else {
                allNodes = tabContents[i].parentNode.querySelectorAll('td');
                var i1;
                for(i1 = 0; i1 < allNodes.length; i1++) {
                    allNodes[i1].style.display = "none";
                }
            }
        }
    }
}

var open = 0;

function removeMobileBar() {
    var bars = document.querySelectorAll(".mobile-side");
    var i;
    for(i = 0; i < bars.length; i++) {
        if(open == 0)
            bars[i].classList.remove("show");
        else if(open < 0)
            open = 0;
        else
            open = open - 1;
    }
}

function toggleMobileBar() {
    var bars = document.querySelectorAll(".mobile-side");
    var i;
    for(i = 0; i < bars.length; i++) {
        bars[i].classList.toggle("show");
    }
    open = open + 1;
}

function holdOpen() {
    open = open + 1;
}


