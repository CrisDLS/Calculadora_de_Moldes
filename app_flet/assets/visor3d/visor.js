// visor.js — Visor 3D interactivo con three.js
let scene, camera, renderer, controls;
let balloonGroup, wireframeGroup;
let lightSun, lightAmbient, lightFlame;
let isNight = true;
let showWireframe = false;
let currentMetadata = null;

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
  camera.up.set(0, 0, 1); // Eje Z hacia arriba

  // 3. Renderer
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(window.devicePixelRatio || 1);
  renderer.shadowMap.enabled = true;
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
  scene.add(balloonGroup);
  scene.add(wireframeGroup);

  // 6. Luces
  lightAmbient = new THREE.AmbientLight(0xffffff, 0.2);
  scene.add(lightAmbient);

  lightSun = new THREE.DirectionalLight(0xfff5e6, 0.4);
  lightSun.position.set(1000, -1500, 2000);
  scene.add(lightSun);

  // Luz de llama interior (cálida, centrada en la boca)
  lightFlame = new THREE.PointLight(0xff7722, 1.5, 3000, 1.2);
  lightFlame.position.set(0, 0, 80);
  scene.add(lightFlame);

  window.addEventListener('resize', onWindowResize);
  animate();
}

function onWindowResize() {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}

function animate() {
  requestAnimationFrame(animate);
  controls.update();

  // Animación suave de parpadeo de la llama interior
  if (lightFlame) {
    const base = parseFloat(document.getElementById('slider-llama').value);
    const flicker = (Math.random() - 0.5) * 0.15;
    lightFlame.intensity = Math.max(0, base + flicker);
  }

  renderer.render(scene, camera);
}

function cargarModelo(data) {
  if (!data || !data.vertices || !data.caras) return;
  currentMetadata = data.metadata;

  // Actualizar tarjeta de info
  if (currentMetadata) {
    const txt = `Altura: ${currentMetadata.altura_total.toFixed(1)} cm · Ancho con picos: ${currentMetadata.ancho_con_picos.toFixed(1)} cm · ${currentMetadata.num_gajos} gajos`;
    document.getElementById('txt-dimensiones').innerText = txt;
  }

  // Limpiar grupos anteriores
  while (balloonGroup.children.length > 0) {
    const obj = balloonGroup.children[0];
    if (obj.geometry) obj.geometry.dispose();
    if (obj.material) {
      if (Array.isArray(obj.material)) obj.material.forEach(m => m.dispose());
      else obj.material.dispose();
    }
    balloonGroup.remove(obj);
  }

  while (wireframeGroup.children.length > 0) {
    const obj = wireframeGroup.children[0];
    if (obj.geometry) obj.geometry.dispose();
    wireframeGroup.remove(obj);
  }

  const verts = data.vertices;
  const caras = data.caras;

  // Agrupar triángulos por color para optimizar draw calls
  const gruposPorColor = {};
  caras.forEach(c => {
    const col = c.color.toLowerCase();
    if (!gruposPorColor[col]) {
      gruposPorColor[col] = [];
    }
    gruposPorColor[col].push(c);
  });

  // Construir mallas por color
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

      // Usar normal calculada de la cara para sombreado facetado realista de papel plegado
      const n = c.normal;
      normals.push(n[0], n[1], n[2]);
      normals.push(n[0], n[1], n[2]);
      normals.push(n[0], n[1], n[2]);
    });

    const geom = new THREE.BufferGeometry();
    geom.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    geom.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));

    // Material de papel china: doble cara, rugoso (roughness alta, specular bajo)
    const mat = new THREE.MeshStandardMaterial({
      color: new THREE.Color(hexColor),
      side: THREE.DoubleSide,
      roughness: 0.85,
      metalness: 0.05,
      flatShading: true,
    });

    const mesh = new THREE.Mesh(geom, mat);
    balloonGroup.add(mesh);

    // Wireframe de aristas
    const wireframeGeom = new THREE.WireframeGeometry(geom);
    const wireframeMat = new THREE.LineBasicMaterial({
      color: 0x444455,
      transparent: true,
      opacity: 0.4
    });
    const wireframeMesh = new THREE.LineSegments(wireframeGeom, wireframeMat);
    wireframeMesh.visible = showWireframe;
    wireframeGroup.add(wireframeMesh);
  });

  // Ajustar posición de la llama según la boca
  if (data.metadata && data.metadata.bbox) {
    const c = data.metadata.bbox.centro;
    lightFlame.position.set(0, 0, Math.max(30, c[2] * 0.3));
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

function setupEvents() {
  const btnDia = document.getElementById('btn-dia');
  const btnNoche = document.getElementById('btn-noche');
  const sliderLlama = document.getElementById('slider-llama');
  const sliderSol = document.getElementById('slider-sol');
  const valLlama = document.getElementById('val-llama');
  const valSol = document.getElementById('val-sol');
  const btnWireframe = document.getElementById('btn-wireframe');
  const btnReset = document.getElementById('btn-reset');

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
    lightAmbient.intensity = 0.2;
    lightSun.intensity = 0.3;
    sliderSol.value = 0.3;
    valSol.innerText = '0.3';
  });

  sliderLlama.addEventListener('input', (e) => {
    valLlama.innerText = e.target.value;
    lightFlame.intensity = parseFloat(e.target.value);
  });

  sliderSol.addEventListener('input', (e) => {
    valSol.innerText = e.target.value;
    const v = parseFloat(e.target.value);
    lightSun.intensity = v;
    lightAmbient.intensity = isNight ? v * 0.5 : v * 0.8;
  });

  btnWireframe.addEventListener('click', () => {
    showWireframe = !showWireframe;
    btnWireframe.classList.toggle('active', showWireframe);
    wireframeGroup.children.forEach(w => { w.visible = showWireframe; });
  });

  btnReset.addEventListener('click', () => {
    resetCamara();
  });
}

// Sondeo automático a la API local de datos
let ultimoHash = '';
function startAutoPoll() {
  // Si estamos en un HTML autocontenido embebido con datos incrustados
  if (window.__DATOS_ESCENA_3D__) {
    cargarModelo(window.__DATOS_ESCENA_3D__);
    resetCamara();
    document.getElementById('status-badge').innerText = 'Autocontenido';
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
      .catch(err => {
        document.getElementById('status-badge').innerText = 'Desconectado';
        document.getElementById('status-badge').style.color = '#f87171';
      });
  }

  poll();
  setInterval(poll, 1500);
}
