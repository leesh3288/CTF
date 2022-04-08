function onKeyDown(e) {
    if ((e.ctrlKey || e.metaKey) && (e.keyCode == 13 || e.keyCode == 10)) {
        fetch("/render", {
                method: "POST",
                headers: {'Content-Type': 'text/markdown'}, 
                body: document.getElementById("code").value,
            }).then(res => res.text())
            .then(resText => document.getElementById("html").innerHTML = resText);
    }
}