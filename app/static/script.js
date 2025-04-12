document.addEventListener('DOMContentLoaded', function() {
    // Toggle proxy fields visibility
    document.getElementById('useProxy').addEventListener('change', function() {
        document.getElementById('proxyFields').style.display = this.checked ? 'block' : 'none';
    });
    
    // Toggle proxy type fields
    document.getElementById('httpProxyType').addEventListener('change', function() {
        if (this.checked) {
            document.getElementById('httpProxyFields').style.display = 'block';
            document.getElementById('socks5ProxyFields').style.display = 'none';
        }
    });
    
    document.getElementById('socks5ProxyType').addEventListener('change', function() {
        if (this.checked) {
            document.getElementById('httpProxyFields').style.display = 'none';
            document.getElementById('socks5ProxyFields').style.display = 'block';
        }
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
            const proxyType = document.querySelector('input[name="proxyType"]:checked').value;
            
            if (proxyType === 'http') {
                const httpProxy = document.getElementById('httpProxy').value;
                const httpsProxy = document.getElementById('httpsProxy').value;
                
                if (httpProxy || httpsProxy) {
                    requestData.proxy = {};
                    if (httpProxy) requestData.proxy.http = httpProxy;
                    if (httpsProxy) requestData.proxy.https = httpsProxy;
                }
            } else if (proxyType === 'socks5') {
                const socks5Proxy = document.getElementById('socks5Proxy').value;
                
                if (socks5Proxy) {
                    requestData.proxy = {
                        socks5: socks5Proxy
                    };
                }
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
            
            // Clear previous response details to avoid showing stale data
            document.getElementById('responseDetails').textContent = '';
            
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
                document.getElementById('responseMessage').textContent = data.message || data.error || 'Unknown error occurred';
                document.getElementById('tweetLink').style.display = 'none';
            }
            
            // Display request details
            if (data.request) {
                document.getElementById('requestDetails').textContent = JSON.stringify(data.request, null, 2);
            } else {
                document.getElementById('requestDetails').textContent = '';
            }
            
            // Display response details - handle both success and error cases
            if (data.status === 'success' && data.response) {
                document.getElementById('responseDetails').textContent = JSON.stringify(data.response, null, 2);
            } else if (data.status === 'error' && data.response) {
                // For error responses, display the response details
                document.getElementById('responseDetails').textContent = JSON.stringify(data.response, null, 2);
            } else if (data.status === 'error') {
                // If no response details but we have an error message, create a simple error object
                const errorObj = {
                    status: 'error',
                    error: data.message || data.error || 'Unknown error occurred'
                };
                document.getElementById('responseDetails').textContent = JSON.stringify(errorObj, null, 2);
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
            
            // Clear request details
            document.getElementById('requestDetails').textContent = '';
            
            // Display error in response details
            const errorObj = {
                status: 'error',
                error: 'Failed to connect to the server: ' + error.message
            };
            document.getElementById('responseDetails').textContent = JSON.stringify(errorObj, null, 2);
        });
    }
});
