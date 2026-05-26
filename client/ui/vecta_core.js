const THREE = require('three');

class VectaCore {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(75, this.container.clientWidth / this.container.clientHeight, 0.1, 1000);
        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });

        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.container.appendChild(this.renderer.domElement);

        this.particles = null;
        this.state = 'IDLE'; // IDLE, LISTENING, THINKING, SPEAKING
        this.init();
        this.animate();

        window.addEventListener('resize', () => this.onWindowResize());
    }

    init() {
        // Create Particle Sphere
        const geometry = new THREE.BufferGeometry();
        const vertices = [];
        const particleCount = 5000;

        for (let i = 0; i < particleCount; i++) {
            const phi = Math.acos(-1 + (2 * i) / particleCount);
            const theta = Math.sqrt(particleCount * Math.PI) * phi;

            const x = 2 * Math.cos(theta) * Math.sin(phi);
            const y = 2 * Math.sin(theta) * Math.sin(phi);
            const z = 2 * Math.cos(phi);

            vertices.push(x, y, z);
        }

        geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));

        const material = new THREE.PointsMaterial({
            color: 0x00d4ff,
            size: 0.02,
            transparent: true,
            opacity: 0.8,
            blending: THREE.AdditiveBlending
        });

        this.particles = new THREE.Points(geometry, material);
        this.scene.add(this.particles);

        this.camera.position.z = 5;

        // Add Bloom effect simulation with light
        const light = new THREE.PointLight(0x00d4ff, 2, 100);
        light.position.set(0, 0, 0);
        this.scene.add(light);
    }

    setState(state) {
        console.log(`VECTA State changed to: ${state}`);
        this.state = state;
    }

    onWindowResize() {
        this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    }

    animate() {
        requestAnimationFrame(() => this.animate());

        const time = Date.now() * 0.001;

        if (this.particles) {
            this.particles.rotation.y += 0.005;
            this.particles.rotation.x += 0.002;

            // Pulse the scale for performance instead of modifying individual particles
            let scale = 1.0;
            if (this.state === 'LISTENING') scale = 1.1 + Math.sin(time * 10) * 0.1;
            if (this.state === 'THINKING') scale = 1.0 + Math.sin(time * 20) * 0.05;
            if (this.state === 'SPEAKING') scale = 1.2 + Math.sin(time * 15) * 0.15;
            if (this.state === 'IDLE') scale = 1.0 + Math.sin(time * 2) * 0.05;

            this.particles.scale.set(scale, scale, scale);
        }

        this.renderer.render(this.scene, this.camera);
    }
}

module.exports = VectaCore;
