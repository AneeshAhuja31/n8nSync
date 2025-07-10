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
            credentials:'include'
        });
    } catch(error){
        console.error('Logout error: ',error);
    }
    localStorage.removeItem('userName');
    localStorage.removeItem('userEmail');
    window.location.href = 'http://localhost:3000/login.html';
}

const storedName = localStorage.getItem('userName');
const storedEmail = localStorage.getItem('userEmail');
if (storedName){
    document.getElementById('welcome').innerText = `Welcome ${storedName}.`;
}

document.addEventListener('DOMContentLoaded',async()=>{
    const storedName = localStorage.getItem('userName');
    const storedEmail = localStorage.getItem('userEmail');
    if (storedName){
        document.getElementById('welcome').innerText = `Welcome ${storedName}.`;
    }
    await validateAuth();

    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
})


