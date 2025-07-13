async function validateAuth() {
    try{
        const response = await fetch("http://localhost:8000/auth/validate/",{
            method:"GET",
            credentials:"include" //include cookies
        })

        if(response.ok){
            const data = await response.json();
            if(data.valid){
                localStorage.setItem('userName',data.user.name);
                localStorage.setItem('userEmail',data.user.email);
                return true;
            }
        }
        window.location.href = 'http://localhost:3000/login.html';
        return false;
    }
    catch (error){
        console.error('Auth validation error: ',error);
        window.location.href = 'http://localhost:3000/login.html';
        return false;
    }
}

async function logout() {
    try{
        await fetch('http://localhost:8000/auth/logout',{
            method:'POST',
            credentials:'include',
            body:JSON.stringify({
                "email":localStorage.getItem("userEmail")
            })
        });
    } catch(error){
        console.error('Logout error: ',error);
    }
    localStorage.removeItem('userName');
    localStorage.removeItem('userEmail');
    localStorage.removeItem('n8nApiKey');  
    localStorage.removeItem('geminiApiKey');
    window.location.href = 'http://localhost:3000/login.html';
}

const storedName = localStorage.getItem('userName');
const storedEmail = localStorage.getItem('userEmail');
if (storedName){
    document.getElementById('welcome').innerText = `Welcome ${storedName}.`;
}

document.addEventListener('DOMContentLoaded',async()=>{
    checkApiKeys();
    const storedName = localStorage.getItem('userName');
    const storedEmail = localStorage.getItem('userEmail');
    const logoutBtn = document.getElementById('logoutBtn');
    const apiKeyForm = document.getElementById('apiKeyForm');
    const instanceTypeSelect = document.getElementById("n8nInstanceType");
    const cloudUriInput = document.getElementById("n8nCloudUri");
    if (storedName){
        document.getElementById('welcome').innerText = `Welcome ${storedName}.`;
    }
    await validateAuth();

    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }

    if(instanceTypeSelect){
        instanceTypeSelect.addEventListener("change",function(){
            if (this.value === "cloud"){
                cloudUriInput.style.display = "block";
                cloudUriInput.required = true;
            } 
            else {
                cloudUriInput.style.display = 'none';
                cloudUriInput.required = false;
                cloudUriInput.value = ''; 
            }
        });
    }

    if (apiKeyForm) {
        apiKeyForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const instanceType = document.getElementById("n8nInstanceType").value;
            const n8nCloudUri = document.getElementById("n8nCloudUri").value.trim();
            const n8nApiKey = document.getElementById('n8nApiKey').value.trim();
            const geminiApiKey = document.getElementById('geminiApiKey').value.trim();

            if (instanceType && n8nApiKey && geminiApiKey) {
                if (instanceType === 'cloud' && !n8nCloudUri) {
                    alert('Please enter the n8n Cloud URI');
                    return;
                }
                
                saveApiKeys(instanceType, n8nCloudUri, n8nApiKey, geminiApiKey);
            }
        });
    }
    
})



function checkApiKeys() {
    const n8nApiKey = localStorage.getItem('n8nApiKey');
    const geminiApiKey = localStorage.getItem('geminiApiKey');
    const n8nInstanceType = localStorage.getItem('n8nInstanceType');
    
    if (!n8nApiKey || !geminiApiKey || !n8nInstanceType) {
        showApiKeyOverlay();
        return false;
    }
    return true;
}

function saveApiKeys(instanceType, cloudUri, n8nApiKey, geminiApiKey) {
    localStorage.setItem('n8nInstanceType', instanceType);
    localStorage.setItem('n8nApiKey', n8nApiKey);
    localStorage.setItem('geminiApiKey', geminiApiKey);
    
    if (instanceType === 'cloud') {
        localStorage.setItem('n8nCloudUri', cloudUri);
    } else {
        localStorage.removeItem('n8nCloudUri');
    }
    
    hideApiKeyOverlay();
}

function showApiKeyOverlay() {
    const overlay = document.getElementById('apiKeyOverlay');
    const container = document.querySelector('.container');
    
    overlay.style.display = 'flex';
    container.classList.add('blurred');
}

function hideApiKeyOverlay() {
    const overlay = document.getElementById('apiKeyOverlay');
    const container = document.querySelector('.container');
    
    overlay.style.display = 'none';
    container.classList.remove('blurred');
}

