function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
const csrftoken = getCookie('csrftoken');

document.querySelectorAll('button[data-rate]').forEach((btn) => {
    btn.addEventListener('click', async (e) => {
        e.preventDefault();

        const kind = btn.dataset.rate;                 // "question" | "answer"
        const id = btn.dataset.id;
        const value = Number(btn.dataset.value);        // 1 или -1

        const counter = document.querySelector(
            `span[data-rating-for="${kind}-${id}"]`
        );

        const url = kind === 'question'
            ? `/questions/${id}/rate/`
            : `/answers/${id}/rate/`;

        const request = new Request(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/json',
            },
            mode: 'same-origin',
            body: JSON.stringify({ value }),
        });

        try {
            const response = await fetch(request);
            if (!response.ok) throw new Error(response.status);
            const data = await response.json();
            counter.innerText = data.rating;
        } catch (err) {
            console.error('rate failed', err);
        }
    });
});