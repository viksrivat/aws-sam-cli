import json
import sys
import time


def handler(event, context):
    return {"statusCode": 200, "body": json.dumps({"hello": "world"})}


def cdk_hello_world(event, context):
    source_ip = event.get("identity", {}).get("sourceIp", "127.0.0.1")
    return {"statusCode": 200, "body":
        """
        <center><h2>AWS-CDK stacks work in SAM-CLI!</h2><center><br/>Run with cdk synth > output.yaml and sam-cli local start-api output.yaml<br/> 
        The current url is <a href="https://{source_ip}{path}">https://{source_ip}{path}</a>.""".format(
            path=event.get("path"), source_ip=source_ip) +
        """
        <script>
        var confetti = {
            maxCount: 150,		//set max confetti count
            speed: 2,			//set the particle animation speed
            frameInterval: 15,	//the confetti animation frame interval in milliseconds
            alpha: 1.0,			//the alpha opacity of the confetti (between 0 and 1, where 1 is opaque and 0 is invisible)
            gradient: false,	//whether to use gradients for the confetti particles
            start: null,		//call to start confetti animation (with optional timeout in milliseconds, and optional min and max random confetti count)
            stop: null,			//call to stop adding confetti
            toggle: null,		//call to start or stop the confetti animation depending on whether it's already running
            pause: null,		//call to freeze confetti animation
            resume: null,		//call to unfreeze confetti animation
            togglePause: null,	//call to toggle whether the confetti animation is paused
            remove: null,		//call to stop the confetti animation and remove all confetti immediately
            isPaused: null,		//call and returns true or false depending on whether the confetti animation is paused
            isRunning: null		//call and returns true or false depending on whether the animation is running
        };
        
            confetti.start = startConfetti;
            confetti.stop = stopConfetti;
            confetti.toggle = toggleConfetti;
            confetti.pause = pauseConfetti;
            confetti.resume = resumeConfetti;
            confetti.togglePause = toggleConfettiPause;
            confetti.isPaused = isConfettiPaused;
            confetti.remove = removeConfetti;
            confetti.isRunning = isConfettiRunning;
            var supportsAnimationFrame = window.requestAnimationFrame || window.webkitRequestAnimationFrame || window.mozRequestAnimationFrame || window.oRequestAnimationFrame || window.msRequestAnimationFrame;
            var colors = ["rgba(30,144,255,", "rgba(107,142,35,", "rgba(255,215,0,", "rgba(255,192,203,", "rgba(106,90,205,", "rgba(173,216,230,", "rgba(238,130,238,", "rgba(152,251,152,", "rgba(70,130,180,", "rgba(244,164,96,", "rgba(210,105,30,", "rgba(220,20,60,"];
            var streamingConfetti = false;
            var animationTimer = null;
            var pause = false;
            var lastFrameTime = Date.now();
            var particles = [];
            var waveAngle = 0;
            var context = null;
        
            function resetParticle(particle, width, height) {
                particle.color = colors[(Math.random() * colors.length) | 0] + (confetti.alpha + ")");
                particle.color2 = colors[(Math.random() * colors.length) | 0] + (confetti.alpha + ")");
                particle.x = Math.random() * width;
                particle.y = Math.random() * height - height;
                particle.diameter = Math.random() * 10 + 5;
                particle.tilt = Math.random() * 10 - 10;
                particle.tiltAngleIncrement = Math.random() * 0.07 + 0.05;
                particle.tiltAngle = 0;
                return particle;
            }
        
            function toggleConfettiPause() {
                if (pause)
                    resumeConfetti();
                else
                    pauseConfetti();
            }
        
            function isConfettiPaused() {
                return pause;
            }
        
            function pauseConfetti() {
                pause = true;
            }
        
            function resumeConfetti() {
                pause = false;
                runAnimation();
            }
        
            function runAnimation() {
                if (pause)
                    return;
                else if (particles.length === 0) {
                    context.clearRect(0, 0, window.innerWidth, window.innerHeight);
                    animationTimer = null;
                } else {
                    var now = Date.now();
                    var delta = now - lastFrameTime;
                    if (!supportsAnimationFrame || delta > confetti.frameInterval) {
                        context.clearRect(0, 0, window.innerWidth, window.innerHeight);
                        updateParticles();
                        drawParticles(context);
                        lastFrameTime = now - (delta % confetti.frameInterval);
                    }
                    animationTimer = requestAnimationFrame(runAnimation);
                }
            }
        
            function startConfetti(timeout, min, max) {
                var width = window.innerWidth;
                var height = window.innerHeight;
                window.requestAnimationFrame = (function() {
                    return window.requestAnimationFrame ||
                        window.webkitRequestAnimationFrame ||
                        window.mozRequestAnimationFrame ||
                        window.oRequestAnimationFrame ||
                        window.msRequestAnimationFrame ||
                        function (callback) {
                            return window.setTimeout(callback, confetti.frameInterval);
                        };
                })();
                var canvas = document.getElementById("confetti-canvas");
                if (canvas === null) {
                    canvas = document.createElement("canvas");
                    canvas.setAttribute("id", "confetti-canvas");
                    canvas.setAttribute("style", "display:block;z-index:999999;pointer-events:none;position:absolute;top:0");
                    document.body.appendChild(canvas);
                    canvas.width = width;
                    canvas.height = height;
                    window.addEventListener("resize", function() {
                        canvas.width = window.innerWidth;
                        canvas.height = window.innerHeight;
                    }, true);
                    context = canvas.getContext("2d");
                }
                var count = confetti.maxCount;
                if (min) {
                    if (max) {
                        if (min == max)
                            count = particles.length + max;
                        else {
                            if (min > max) {
                                var temp = min;
                                min = max;
                                max = temp;
                            }
                            count = particles.length + ((Math.random() * (max - min) + min) | 0);
                        }
                    } else
                        count = particles.length + min;
                } else if (max)
                    count = particles.length + max;
                while (particles.length < count)
                    particles.push(resetParticle({}, width, height));
                streamingConfetti = true;
                pause = false;
                runAnimation();
                if (timeout) {
                    window.setTimeout(stopConfetti, timeout);
                }
            }
        
            function stopConfetti() {
                streamingConfetti = false;
            }
        
            function removeConfetti() {
                stop();
                pause = false;
                particles = [];
            }
        
            function toggleConfetti() {
                if (streamingConfetti)
                    stopConfetti();
                else
                    startConfetti();
            }
            
            function isConfettiRunning() {
                return streamingConfetti;
            }
        
            function drawParticles(context) {
                var particle;
                var x, y, x2, y2;
                for (var i = 0; i < particles.length; i++) {
                    particle = particles[i];
                    context.beginPath();
                    context.lineWidth = particle.diameter;
                    x2 = particle.x + particle.tilt;
                    x = x2 + particle.diameter / 2;
                    y2 = particle.y + particle.tilt + particle.diameter / 2;
                    if (confetti.gradient) {
                        var gradient = context.createLinearGradient(x, particle.y, x2, y2);
                        gradient.addColorStop("0", particle.color);
                        gradient.addColorStop("1.0", particle.color2);
                        context.strokeStyle = gradient;
                    } else
                        context.strokeStyle = particle.color;
                    context.moveTo(x, particle.y);
                    context.lineTo(x2, y2);
                    context.stroke();
                }
            }
        
            function updateParticles() {
                var width = window.innerWidth;
                var height = window.innerHeight;
                var particle;
                waveAngle += 0.01;
                for (var i = 0; i < particles.length; i++) {
                    particle = particles[i];
                    if (!streamingConfetti && particle.y < -15)
                        particle.y = height + 100;
                    else {
                        particle.tiltAngle += particle.tiltAngleIncrement;
                        particle.x += Math.sin(waveAngle);
                        particle.y += (Math.cos(waveAngle) + particle.diameter + confetti.speed) * 0.5;
                        particle.tilt = Math.sin(particle.tiltAngle) * 15;
                    }
                    if (particle.x > width + 20 || particle.x < -20 || particle.y > height) {
                        if (streamingConfetti && particles.length <= confetti.maxCount)
                            resetParticle(particle, width, height);
                        else {
                            particles.splice(i, 1);
                            i--;
                        }
                    }
                }
            }
        startConfetti();
        </script>
        
        """,
            "headers": {"Content-Type": "text/html"}}


def serverless_hello_world(event, context):
    source_ip = event.get("identity", {}).get("sourceIp", "127.0.0.1")
    return {"statusCode": 200, "body":
        """
        <center><h3>Serverless Framework stacks work in SAM-CLI!</h3><center><br/> The url is <a href="https://{source_ip}{path}">https://{source_ip}{path}</a>.""".format(
            path=event.get("path"), source_ip=source_ip) +
        """
        <script>
        var confetti = {
            maxCount: 150,		//set max confetti count
            speed: 2,			//set the particle animation speed
            frameInterval: 15,	//the confetti animation frame interval in milliseconds
            alpha: 1.0,			//the alpha opacity of the confetti (between 0 and 1, where 1 is opaque and 0 is invisible)
            gradient: false,	//whether to use gradients for the confetti particles
            start: null,		//call to start confetti animation (with optional timeout in milliseconds, and optional min and max random confetti count)
            stop: null,			//call to stop adding confetti
            toggle: null,		//call to start or stop the confetti animation depending on whether it's already running
            pause: null,		//call to freeze confetti animation
            resume: null,		//call to unfreeze confetti animation
            togglePause: null,	//call to toggle whether the confetti animation is paused
            remove: null,		//call to stop the confetti animation and remove all confetti immediately
            isPaused: null,		//call and returns true or false depending on whether the confetti animation is paused
            isRunning: null		//call and returns true or false depending on whether the animation is running
        };

            confetti.start = startConfetti;
            confetti.stop = stopConfetti;
            confetti.toggle = toggleConfetti;
            confetti.pause = pauseConfetti;
            confetti.resume = resumeConfetti;
            confetti.togglePause = toggleConfettiPause;
            confetti.isPaused = isConfettiPaused;
            confetti.remove = removeConfetti;
            confetti.isRunning = isConfettiRunning;
            var supportsAnimationFrame = window.requestAnimationFrame || window.webkitRequestAnimationFrame || window.mozRequestAnimationFrame || window.oRequestAnimationFrame || window.msRequestAnimationFrame;
            var colors = ["rgba(30,144,255,", "rgba(107,142,35,", "rgba(255,215,0,", "rgba(255,192,203,", "rgba(106,90,205,", "rgba(173,216,230,", "rgba(238,130,238,", "rgba(152,251,152,", "rgba(70,130,180,", "rgba(244,164,96,", "rgba(210,105,30,", "rgba(220,20,60,"];
            var streamingConfetti = false;
            var animationTimer = null;
            var pause = false;
            var lastFrameTime = Date.now();
            var particles = [];
            var waveAngle = 0;
            var context = null;

            function resetParticle(particle, width, height) {
                particle.color = colors[(Math.random() * colors.length) | 0] + (confetti.alpha + ")");
                particle.color2 = colors[(Math.random() * colors.length) | 0] + (confetti.alpha + ")");
                particle.x = Math.random() * width;
                particle.y = Math.random() * height - height;
                particle.diameter = Math.random() * 10 + 5;
                particle.tilt = Math.random() * 10 - 10;
                particle.tiltAngleIncrement = Math.random() * 0.07 + 0.05;
                particle.tiltAngle = 0;
                return particle;
            }

            function toggleConfettiPause() {
                if (pause)
                    resumeConfetti();
                else
                    pauseConfetti();
            }

            function isConfettiPaused() {
                return pause;
            }

            function pauseConfetti() {
                pause = true;
            }

            function resumeConfetti() {
                pause = false;
                runAnimation();
            }

            function runAnimation() {
                if (pause)
                    return;
                else if (particles.length === 0) {
                    context.clearRect(0, 0, window.innerWidth, window.innerHeight);
                    animationTimer = null;
                } else {
                    var now = Date.now();
                    var delta = now - lastFrameTime;
                    if (!supportsAnimationFrame || delta > confetti.frameInterval) {
                        context.clearRect(0, 0, window.innerWidth, window.innerHeight);
                        updateParticles();
                        drawParticles(context);
                        lastFrameTime = now - (delta % confetti.frameInterval);
                    }
                    animationTimer = requestAnimationFrame(runAnimation);
                }
            }

            function startConfetti(timeout, min, max) {
                var width = window.innerWidth;
                var height = window.innerHeight;
                window.requestAnimationFrame = (function() {
                    return window.requestAnimationFrame ||
                        window.webkitRequestAnimationFrame ||
                        window.mozRequestAnimationFrame ||
                        window.oRequestAnimationFrame ||
                        window.msRequestAnimationFrame ||
                        function (callback) {
                            return window.setTimeout(callback, confetti.frameInterval);
                        };
                })();
                var canvas = document.getElementById("confetti-canvas");
                if (canvas === null) {
                    canvas = document.createElement("canvas");
                    canvas.setAttribute("id", "confetti-canvas");
                    canvas.setAttribute("style", "display:block;z-index:999999;pointer-events:none;position:absolute;top:0");
                    document.body.appendChild(canvas);
                    canvas.width = width;
                    canvas.height = height;
                    window.addEventListener("resize", function() {
                        canvas.width = window.innerWidth;
                        canvas.height = window.innerHeight;
                    }, true);
                    context = canvas.getContext("2d");
                }
                var count = confetti.maxCount;
                if (min) {
                    if (max) {
                        if (min == max)
                            count = particles.length + max;
                        else {
                            if (min > max) {
                                var temp = min;
                                min = max;
                                max = temp;
                            }
                            count = particles.length + ((Math.random() * (max - min) + min) | 0);
                        }
                    } else
                        count = particles.length + min;
                } else if (max)
                    count = particles.length + max;
                while (particles.length < count)
                    particles.push(resetParticle({}, width, height));
                streamingConfetti = true;
                pause = false;
                runAnimation();
                if (timeout) {
                    window.setTimeout(stopConfetti, timeout);
                }
            }

            function stopConfetti() {
                streamingConfetti = false;
            }

            function removeConfetti() {
                stop();
                pause = false;
                particles = [];
            }

            function toggleConfetti() {
                if (streamingConfetti)
                    stopConfetti();
                else
                    startConfetti();
            }

            function isConfettiRunning() {
                return streamingConfetti;
            }

            function drawParticles(context) {
                var particle;
                var x, y, x2, y2;
                for (var i = 0; i < particles.length; i++) {
                    particle = particles[i];
                    context.beginPath();
                    context.lineWidth = particle.diameter;
                    x2 = particle.x + particle.tilt;
                    x = x2 + particle.diameter / 2;
                    y2 = particle.y + particle.tilt + particle.diameter / 2;
                    if (confetti.gradient) {
                        var gradient = context.createLinearGradient(x, particle.y, x2, y2);
                        gradient.addColorStop("0", particle.color);
                        gradient.addColorStop("1.0", particle.color2);
                        context.strokeStyle = gradient;
                    } else
                        context.strokeStyle = particle.color;
                    context.moveTo(x, particle.y);
                    context.lineTo(x2, y2);
                    context.stroke();
                }
            }

            function updateParticles() {
                var width = window.innerWidth;
                var height = window.innerHeight;
                var particle;
                waveAngle += 0.01;
                for (var i = 0; i < particles.length; i++) {
                    particle = particles[i];
                    if (!streamingConfetti && particle.y < -15)
                        particle.y = height + 100;
                    else {
                        particle.tiltAngle += particle.tiltAngleIncrement;
                        particle.x += Math.sin(waveAngle);
                        particle.y += (Math.cos(waveAngle) + particle.diameter + confetti.speed) * 0.5;
                        particle.tilt = Math.sin(particle.tiltAngle) * 15;
                    }
                    if (particle.x > width + 20 || particle.x < -20 || particle.y > height) {
                        if (streamingConfetti && particles.length <= confetti.maxCount)
                            resetParticle(particle, width, height);
                        else {
                            particles.splice(i, 1);
                            i--;
                        }
                    }
                }
            }
        startConfetti();
        </script>

        """,
            "headers": {"Content-Type": "text/html"}}


def echo_event_handler(event, context):
    return {"statusCode": 200, "body": json.dumps(event)}


def echo_event_handler_2(event, context):
    event['handler'] = 'echo_event_handler_2'

    return {"statusCode": 200, "body": json.dumps(event)}


def content_type_setter_handler(event, context):
    return {"statusCode": 200, "body": "hello", "headers": {"Content-Type": "text/plain"}}


def only_set_status_code_handler(event, context):
    return {"statusCode": 200}


def only_set_body_handler(event, context):
    return {"body": json.dumps({"hello": "world"})}


def string_status_code_handler(event, context):
    return {"statusCode": "200", "body": json.dumps({"hello": "world"})}


def sleep_10_sec_handler(event, context):
    # sleep thread for 10s. This is useful for testing multiple requests
    time.sleep(10)

    return {"statusCode": 200, "body": json.dumps({"message": "HelloWorld! I just slept and waking up."})}


def write_to_stderr(event, context):
    sys.stderr.write("Docker Lambda is writing to stderr")

    return {"statusCode": 200, "body": json.dumps({"hello": "world"})}


def write_to_stdout(event, context):
    sys.stdout.write("Docker Lambda is writing to stdout")

    return {"statusCode": 200, "body": json.dumps({"hello": "world"})}


def invalid_response_returned(event, context):
    return "This is invalid"


def invalid_hash_response(event, context):
    return {"foo": "bar"}


def base64_response(event, context):
    gifImageBase64 = "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"  # NOQA

    return {
        "statusCode": 200,
        "body": gifImageBase64,
        "isBase64Encoded": True,
        "headers": {
            "Content-Type": "image/gif"
        }
    }


def echo_base64_event_body(event, context):
    return {
        "statusCode": 200,
        "body": event["body"],
        "headers": {
            "Content-Type": event["headers"]["Content-Type"]
        },
        "isBase64Encoded": event["isBase64Encoded"]
    }


def multiple_headers(event, context):
    return {
        "statusCode": 200,
        "body": "hello",
        "headers": {"Content-Type": "text/plain"},
        "multiValueHeaders": {"MyCustomHeader": ['Value1', 'Value2']}
    }


def multiple_headers_overrides_headers(event, context):
    return {
        "statusCode": 200,
        "body": "hello",
        "headers": {"Content-Type": "text/plain", "MyCustomHeader": 'Custom'},
        "multiValueHeaders": {"MyCustomHeader": ['Value1', 'Value2']}
    }
