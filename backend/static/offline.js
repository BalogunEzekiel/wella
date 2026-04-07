function saveOffline(data) {
    let patients = JSON.parse(localStorage.getItem("patients")) || [];
    patients.push(data);
    localStorage.setItem("patients", JSON.stringify(patients));
}