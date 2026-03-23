function simulateAttack() {
    fetch('/simulate', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            alert("Request Rate: " + data.request_rate + 
                  "\nType: " + data.attack_type);
            location.reload();
        });
}