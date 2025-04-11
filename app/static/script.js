document.addEventListener('DOMContentLoaded', function() {
    // Toggle proxy fields visibility
    document.getElementById('useProxy').addEventListener('change', function() {
        document.getElementById('proxyFields').style.display = this.checked ? 'block' : 'none';
    });
    
    // Handle form submission
    document.getElementById('tweetForm').addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Show loading spinner
        document.getElementById('loading').style.display = 'block';
        document.getElementById('response').style.display = 'none';
        document.getElementById('submitBtn').disabled = true;
        
        // Get form data
        const apiKey = document.getElementById('apiKey').value;
        const apiSecret = document.getElementById('apiSecret').value;
        const accessToken = document.getElementById('accessToken').value;
        const accessSecret = document.getElementById('accessSecret').value;
        const tweetText = document.getElementById('tweetText').value;
        const useProxy = document.getElementById('useProxy').checked;
        
        // Prepare request data
        let requestData = {
            api_key: apiKey,
            api_secret: apiSecret,
            access_token: accessToken,
            access_secret: accessSecret,
            text: tweetText
        };
        
        // Add proxy if enabled
        if (useProxy) {
            const httpProxy = document.getElementById('httpProxy').value;
            const httpsProxy = document.getElementById('httpsProxy').value;
            
            if (httpProxy || httpsProxy) {
                requestData.proxy = {};
                if (httpProxy) requestData.proxy.http = httpProxy;
                if (httpsProxy) requestData.proxy.https = httpsProxy;
            }
        }
        
        // Handle image if selected
        const imageFile = document.getElementById('imageFile').files[0];
        if (imageFile) {
            const reader = new FileReader();
            reader.onload = function(event) {
                // Get base64 data without the prefix
                const base64Image = event.target.result.split(',')[1];
                requestData.image = base64Image;
                sendTweetRequest(requestData);
            };
            reader.readAsDataURL(imageFile);
        } else {
            sendTweetRequest(requestData);
        }
    });
    
    function sendTweetRequest(requestData) {
        fetch('/post', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        })
        .then(response => response.json())
        .then(data => {
            // Hide loading spinner
            document.getElementById('loading').style.display = 'none';
            document.getElementById('submitBtn').disabled = false;
            
            // Show response
            const responseElement = document.getElementById('response');
            responseElement.style.display = 'block';
            
            if (data.status === 'success') {
                responseElement.className = 'response success';
                document.getElementById('responseTitle').textContent = 'Tweet Posted Successfully!';
                document.getElementById('responseMessage').textContent = 'Tweet ID: ' + data.tweet_id;
                
                // Show tweet link
                const tweetLink = document.getElementById('tweetLink');
                tweetLink.href = data.tweet_url;
                tweetLink.textContent = 'View Tweet';
                tweetLink.style.display = 'block';
            } else {
                responseElement.className = 'response error';
                document.getElementById('responseTitle').textContent = 'Error';
                document.getElementById('responseMessage').textContent = data.message;
                document.getElementById('tweetLink').style.display = 'none';
            }
        })
        .catch(error => {
            // Hide loading spinner
            document.getElementById('loading').style.display = 'none';
            document.getElementById('submitBtn').disabled = false;
            
            // Show error
            const responseElement = document.getElementById('response');
            responseElement.style.display = 'block';
            responseElement.className = 'response error';
            document.getElementById('responseTitle').textContent = 'Error';
            document.getElementById('responseMessage').textContent = 'Failed to connect to the server: ' + error.message;
            document.getElementById('tweetLink').style.display = 'none';
        });
    }
});
