function sendMail(contactForm) {
    emailjs.send("service_dwqe96l", "Instructor Hours Contact", {
            "first_name": contactForm.firstname.value,
            "last_name": contactForm.lastname.value,
            "from_email": contactForm.emailaddress.value,
            "question": contactForm.question.value
    })
    .then(function(response) {
        console.log("SUCCESS", response);
        alert('Thank you for Submit your question(s).\nWe will reply shortly.');
    },
        function(error) {
            console.log("FAILED", error);}
        );
    document.getElementById("contact-form").reset();
    return false;
}
