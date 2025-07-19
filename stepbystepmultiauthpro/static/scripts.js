document.getElementById('linkedinForm').addEventListener('submit', function(event) {
    event.preventDefault();
    
    const linkedinUrl = document.getElementById('linkedin_url').value;
    if (!linkedinUrl) {
        alert("Please enter a valid LinkedIn URL!");
        return;
    }
    
    fetch('/link_linkedin', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            'linkedin_url': linkedinUrl
        })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('message').innerHTML = data.message || "LinkedIn URL linked successfully!";
        document.getElementById('message').style.color = data.success ? "green" : "red";
    })
    .catch(error => {
        document.getElementById('message').innerHTML = "Error linking LinkedIn profile!";
        document.getElementById('message').style.color = "red";
    });
});