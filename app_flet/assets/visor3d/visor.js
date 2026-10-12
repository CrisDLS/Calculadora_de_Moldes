// visor.js — Visor 3D interactivo con three.js y controles de iluminación
let scene, camera, renderer, controls;
let balloonGroup, wireframeGroup, seamsGroup;
let lightSun, lightAmbient, lightFlame;
let isNight = true;
let showWireframe = false;
let showSeams = true;
let currentMetadata = null;

let sunAzimuthDeg = 45;
let sunElevationDeg = 40;
let sunDistance = 2500;

init();
setupEvents();
startAutoPoll();

function init() {
  const container = document.getElementById('canvas-container');

  // 1. Escena
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x101014);

  // 2. Cámara
  camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 1, 50000);
  camera.position.set(0, -1200, 400);
  camera.up.set(0, 0, 1); // Eje Z vertical hacia arriba

  // 3. Renderer con sombras suaves y mapeo de tonos
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, preserveDrawingBuffer: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(window.devicePixelRatio || 1);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap; // Sombras suaves
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.0;
  container.appendChild(renderer.domElement);

  // 4. Controles orbitales
  controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;
  controls.screenSpacePanning = true;
  controls.minDistance = 50;
  controls.maxDistance = 20000;

  // 5. Grupos de objetos
  balloonGroup = new THREE.Group();
  wireframeGroup = new THREE.Group();
  seamsGroup = new THREE.Group();
  scene.add(balloonGroup);
  scene.add(wireframeGroup);
  scene.add(seamsGroup);

  // 6. Luces
  lightAmbient = new THREE.AmbientLight(0xffffff, 0.25);
  scene.add(lightAmbient);

  lightSun = new THREE.DirectionalLight(0xfff5e6, 0.4);
  lightSun.castShadow = true;
  lightSun.shadow.mapSize.width = 2048;
  lightSun.shadow.mapSize.height = 2048;
  lightSun.shadow.camera.near = 100;
  lightSun.shadow.camera.far = 6000;
  const d = 1000;
  lightSun.shadow.camera.left = -d;
  lightSun.shadow.camera.right = d;
  lightSun.shadow.camera.top = d;
  lightSun.shadow.camera.bottom = -d;
  lightSun.shadow.bias = -0.0005;
  scene.add(lightSun);
  actualizarPosicionSol();

  // Luz de llama interior (cálida, centrada en la boca)
  lightFlame = new THREE.PointLight(0xff7722, 1.5, 3500, 1.2);
  lightFlame.position.set(0, 0, 80);
  scene.add(lightFlame);

  window.addEventListener('resize', onWindowResize);
  animate();
}

function actualizarPosicionSol() {
  const azRad = (sunAzimuthDeg * Math.PI) / 180;
  const elRad = (sunElevationDeg * Math.PI) / 180;
  const x = sunDistance * Math.cos(elRad) * Math.sin(azRad);
  const y = -sunDistance * Math.cos(elRad) * Math.cos(azRad);
  const z = sunDistance * Math.sin(elRad);
  lightSun.position.set(x, y, z);
}

function onWindowResize() {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}

function animate() {
  requestAnimationFrame(animate);
  controls.update();

  // Parpadeo suave realista de la llama interior
  if (lightFlame) {
    const elSlider = document.getElementById('slider-llama');
    const base = elSlider ? parseFloat(elSlider.value) : 1.5;
    const flicker = (Math.random() - 0.5) * 0.15;
    lightFlame.intensity = Math.max(0, base + flicker);
  }

  renderer.render(scene, camera);
}

function cargarModelo(data) {
  if (!data || !data.vertices || !data.caras) return;
  currentMetadata = data.metadata;

  if (currentMetadata) {
    const txt = `Altura: ${currentMetadata.altura_total.toFixed(1)} cm · Ancho con picos: ${currentMetadata.ancho_con_picos.toFixed(1)} cm · ${currentMetadata.num_gajos} gajos`;
    document.getElementById('txt-dimensiones').innerText = txt;
  }

  // Limpiar grupos anteriores
  const limpiar = (grp) => {
    while (grp.children.length > 0) {
      const obj = grp.children[0];
      if (obj.geometry) obj.geometry.dispose();
      if (obj.material) {
        if (Array.isArray(obj.material)) obj.material.forEach(m => m.dispose());
        else obj.material.dispose();
      }
      grp.remove(obj);
    }
  };
  limpiar(balloonGroup);
  limpiar(wireframeGroup);
  limpiar(seamsGroup);

  const verts = data.vertices;
  const caras = data.caras;

  // Agrupar triángulos por color
  const gruposPorColor = {};
  caras.forEach(c => {
    const col = c.color.toLowerCase();
    if (!gruposPorColor[col]) gruposPorColor[col] = [];
    gruposPorColor[col].push(c);
  });

  Object.keys(gruposPorColor).forEach(hexColor => {
    const carasColor = gruposPorColor[hexColor];
    const positions = [];
    const normals = [];

    carasColor.forEach(c => {
      const idx = c.indices;
      const v0 = verts[idx[0]];
      const v1 = verts[idx[1]];
      const v2 = verts[idx[2]];

      positions.push(v0[0], v0[1], v0[2]);
      positions.push(v1[0], v1[1], v1[2]);
      positions.push(v2[0], v2[1], v2[2]);

      const n = c.normal;
      normals.push(n[0], n[1], n[2]);
      normals.push(n[0], n[1], n[2]);
      normals.push(n[0], n[1], n[2]);
    });

    const geom = new THREE.BufferGeometry();
    geom.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    geom.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));

    const mat = new THREE.MeshStandardMaterial({
      color: new THREE.Color(hexColor),
      side: THREE.DoubleSide,
      roughness: 0.85,
      metalness: 0.05,
      flatShading: true,
    });

    const mesh = new THREE.Mesh(geom, mat);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    balloonGroup.add(mesh);

    // Wireframe completo de aristas trianguladas
    const wireGeom = new THREE.WireframeGeometry(geom);
    const wireMat = new THREE.LineBasicMaterial({
      color: 0x555566,
      transparent: true,
      opacity: 0.35
    });
    const wireMesh = new THREE.LineSegments(wireGeom, wireMat);
    wireMesh.visible = showWireframe;
    wireframeGroup.add(wireMesh);

    // Costuras (aristas con ángulo pronunciado / contorno de facetas)
    const edgesGeom = new THREE.EdgesGeometry(geom, 25);
    const seamsMat = new THREE.LineBasicMaterial({
      color: 0x222228,
      linewidth: 1.5,
      transparent: true,
      opacity: 0.75
    });
    const seamsMesh = new THREE.LineSegments(edgesGeom, seamsMat);
    seamsMesh.visible = showSeams;
    seamsGroup.add(seamsMesh);
  });

  // Ajustar posición de llama
  if (data.metadata && data.metadata.bbox) {
    const c = data.metadata.bbox.centro;
    lightFlame.position.set(0, 0, Math.max(30, c[2] * 0.3));
    sunDistance = Math.max(2000, currentMetadata.altura_total * 2.5);
    actualizarPosicionSol();
  }
}

function resetCamara() {
  if (!currentMetadata || !currentMetadata.bbox) return;
  const bbox = currentMetadata.bbox;
  const c = bbox.centro;
  const maxDim = Math.max(
    bbox.max[0] - bbox.min[0],
    bbox.max[1] - bbox.min[1],
    bbox.max[2] - bbox.min[2]
  );

  controls.target.set(c[0], c[1], c[2]);
  camera.position.set(c[0], c[1] - maxDim * 1.8, c[2] + maxDim * 0.4);
  camera.lookAt(c[0], c[1], c[2]);
  controls.update();
}

function guardarImagenPNG() {
  renderer.render(scene, camera);
  const dataURL = renderer.domElement.toDataURL('image/png');
  const link = document.createElement('a');
  link.download = `trompo_estrella_3d_${Date.now()}.png`;
  link.href = dataURL;
  link.click();
}

function setupEvents() {
  const btnDia = document.getElementById('btn-dia');
  const btnNoche = document.getElementById('btn-noche');
  const sliderAzimut = document.getElementById('slider-azimut');
  const sliderElevacion = document.getElementById('slider-elevacion');
  const sliderSol = document.getElementById('slider-sol');
  const sliderLlama = document.getElementById('slider-llama');
  const sliderExposicion = document.getElementById('slider-exposicion');
  const valAzimut = document.getElementById('val-azimut');
  const valElevacion = document.getElementById('val-elevacion');
  const valSol = document.getElementById('val-sol');
  const valLlama = document.getElementById('val-llama');
  const valExposicion = document.getElementById('val-exposicion');
  const btnWireframe = document.getElementById('btn-wireframe');
  const btnCosturas = document.getElementById('btn-costuras');
  const btnReset = document.getElementById('btn-reset');
  const btnCaptura = document.getElementById('btn-captura');

  btnDia.addEventListener('click', () => {
    isNight = false;
    btnDia.classList.add('active');
    btnNoche.classList.remove('active');
    scene.background = new THREE.Color(0xdce5ed);
    lightAmbient.intensity = 0.8;
    lightSun.intensity = 1.0;
    sliderSol.value = 1.0;
    valSol.innerText = '1.0';
  });

  btnNoche.addEventListener('click', () => {
    isNight = true;
    btnNoche.classList.add('active');
    btnDia.classList.remove('active');
    scene.background = new THREE.Color(0x101014);
    lightAmbient.intensity = 0.25;
    lightSun.intensity = 0.4;
    sliderSol.value = 0.4;
    valSol.innerText = '0.4';
  });

  sliderAzimut.addEventListener('input', (e) => {
    sunAzimuthDeg = parseFloat(e.target.value);
    valAzimut.innerText = `${sunAzimuthDeg}°`;
    actualizarPosicionSol();
  });

  sliderElevacion.addEventListener('input', (e) => {
    sunElevationDeg = parseFloat(e.target.value);
    valElevacion.innerText = `${sunElevationDeg}°`;
    actualizarPosicionSol();
  });

  sliderSol.addEventListener('input', (e) => {
    valSol.innerText = e.target.value;
    const v = parseFloat(e.target.value);
    lightSun.intensity = v;
    lightAmbient.intensity = isNight ? v * 0.5 : v * 0.8;
  });

  sliderLlama.addEventListener('input', (e) => {
    valLlama.innerText = e.target.value;
    lightFlame.intensity = parseFloat(e.target.value);
  });

  sliderExposicion.addEventListener('input', (e) => {
    valExposicion.innerText = e.target.value;
    renderer.toneMappingExposure = parseFloat(e.target.value);
  });

  btnWireframe.addEventListener('click', () => {
    showWireframe = !showWireframe;
    btnWireframe.classList.toggle('active', showWireframe);
    wireframeGroup.children.forEach(w => { w.visible = showWireframe; });
  });

  btnCosturas.addEventListener('click', () => {
    showSeams = !showSeams;
    btnCosturas.classList.toggle('active', showSeams);
    seamsGroup.children.forEach(s => { s.visible = showSeams; });
  });

  btnReset.addEventListener('click', resetCamara);
  btnCaptura.addEventListener('click', guardarImagenPNG);
}

// Sondeo automático a la API local
let ultimoHash = '';
function startAutoPoll() {
  if (window.__DATOS_ESCENA_3D__) {
    cargarModelo(window.__DATOS_ESCENA_3D__);
    resetCamara();
    const b = document.getElementById('status-badge');
    if (b) b.innerText = 'Autocontenido';
    return;
  }

  function poll() {
    fetch('/api/escena')
      .then(r => r.json())
      .then(data => {
        const hash = JSON.stringify(data.metadata || {});
        if (hash !== ultimoHash) {
          const primerCargue = (ultimoHash === '');
          ultimoHash = hash;
          cargarModelo(data);
          if (primerCargue) resetCamara();
        }
      })
      .catch(() => {
        const b = document.getElementById('status-badge');
        if (b) {
          b.innerText = 'Desconectado';
          b.style.color = '#f87171';
        }
      });
  }

  poll();
  setInterval(poll, 1500);
}
