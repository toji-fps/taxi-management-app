const form = document.querySelector("#booking-form");
const message = document.querySelector("#booking-message");

function setMessage(text, type = "") {
  message.textContent = text;
  message.className = `message span-2 ${type}`.trim();
}

function payloadFromForm(formElement) {
  return Object.fromEntries(new FormData(formElement).entries());
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!form.checkValidity()) {
    form.reportValidity();
    return;
  }

  const button = form.querySelector("button[type='submit']");
  button.disabled = true;
  button.textContent = "Submitting...";
  setMessage("");

  try {
    const response = await fetch("/api/book", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payloadFromForm(form)),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Unable to submit booking");
    form.reset();
    form.passenger_count.value = "1";
    setMessage("Your booking request was sent successfully.", "success");
  } catch (error) {
    setMessage(error.message, "error");
  } finally {
    button.disabled = false;
    button.textContent = "Submit booking";
  }
});
