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
document.addEventListener('DOMContentLoaded', () => {
    const csrftoken = getCookie('csrftoken');

    document.querySelectorAll('button[data-rate]').forEach((btn) => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();

            const kind = btn.dataset.rate;            // "question" | "answer"
            const id = btn.dataset.id;
            const value = Number(btn.dataset.value);

            const wrap = btn.closest('.vote');
            const counter = wrap?.querySelector(`span[data-rating-for="${kind}-${id}"]`);
            const upBtn = wrap?.querySelector('.up');
            const downBtn = wrap?.querySelector('.down');
            if (!counter) return;

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

            btn.disabled = true;
            try {
                const response = await fetch(request);

                if (response.redirected) {
                    window.location.href = response.url;
                    return;
                }
                if (!response.ok) throw new Error(response.status);

                const data = await response.json();
                counter.innerText = data.rating;
                upBtn?.classList.toggle('active', data.user_value === 1);
                downBtn?.classList.toggle('active', data.user_value === -1);
            } catch (err) {
                console.error('rate failed', err);
            } finally {
                btn.disabled = false;
            }
        });
    });


    const checkboxes = document.querySelectorAll('.js-mark-correct');

    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function () {
            const questionId = this.dataset.questionId;
            const answerId = this.dataset.answerId;
            const url = `/questions/${questionId}/${answerId}/correct/`;

            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    is_correct: this.checked
                })
            })
                .then(response => {
                    if (!response.ok) {
                        this.checked = !this.checked;
                        throw new Error('Ошибка сервера');
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('Статус обновлён:', data.is_correct);
                })
                .catch(error => {
                    console.error('Ошибка:', error);
                });
        });
    });

});