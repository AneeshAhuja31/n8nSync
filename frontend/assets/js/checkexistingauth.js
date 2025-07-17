async function checkexistingAuth() {
    try{
        const response = await fetch("http://localhost:8000/auth/validate",{
            method:"GET",
            credentials:"include" //include cookies
        })
        if(response.ok){
            const data = await response.json();
            if(data.valid){
                window.location.href = 'http://localhost:3000/chat'
                return;
            }
        }
    }
    catch (error){
        console.error('Auth validation error: ',error);
    }
}
document.addEventListener('DOMContentLoaded',async()=>{
    await checkexistingAuth();
})

