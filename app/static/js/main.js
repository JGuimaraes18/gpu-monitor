document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById("search");
    const items = document.querySelectorAll(".machine-item");

    searchInput.addEventListener("input", (e) => {
        const value = e.target.value.toLowerCase();
        items.forEach(item => {
            const name = item.dataset.name.toLowerCase();
            item.style.display = name.includes(value) ? "flex" : "none";
        });
    });
});
