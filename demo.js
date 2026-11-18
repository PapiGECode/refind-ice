const labels = ["Windows", "Linux", "Información", "Reiniciar", "Apagar", "Salir", "BIOS"];
const symbols = ["⊞", ">_", "ⓘ", "↻", "⏻", "⇥", "▦"];
const viewport = document.querySelector("#viewport");
const capture = document.querySelector("#capture");
const monitor = document.querySelector(".monitor");
const zoom = document.querySelector("#zoom");
const full = document.querySelector("#full");
const choices = [];
const targets = [];
let selection = 0;
let resolution = "4k";
let lastSystem = 0;
let lastTool = 2;

labels.forEach((label, index) => {
  const button = document.createElement("button");
  button.className = "choice";
  const symbol = document.createElement("span");
  symbol.className = "symbol";
  symbol.setAttribute("aria-hidden", "true");
  symbol.textContent = symbols[index];
  button.append(symbol, document.createTextNode(label));
  button.onclick = () => select(index);
  document.querySelector(index < 2 ? "#systems" : "#tools").append(button);
  choices.push(button);
  const target = document.createElement("span");
  target.className = "hit";
  target.title = label;
  target.onclick = () => select(index);
  document.querySelector("#targets").append(target);
  targets.push(target);
});

function select(index) {
  selection = index;
  if (index < 2) lastSystem = index;
  else lastTool = index;
  choices.forEach((button, i) => button.setAttribute("aria-pressed", String(i === index)));
  capture.alt = "Menú ICE con " + labels[index] + " seleccionado";
  capture.src = resolution + "/vm-" + index + ".png";
  document.querySelector("#status").textContent = labels[index] + " · " + resolution.toUpperCase();
  if (viewport.classList.contains("native")) centerSelection();
}

function centerSelection() {
  const icon = targets[selection];
  viewport.scrollLeft = icon.offsetLeft + icon.offsetWidth / 2 - viewport.clientWidth / 2;
  viewport.scrollTop = icon.offsetTop + icon.offsetHeight / 2 - viewport.clientHeight / 2;
}

function setResolution(value) {
  resolution = value;
  const scale = value === "4k" ? 2 : 1;
  const width = 1920 * scale, height = 1080 * scale;
  viewport.style.setProperty("--native-width", width + "px");
  document.querySelector("#dimensions").textContent = width + " × " + height;
  document.querySelectorAll("[data-res]").forEach(button => {
    button.setAttribute("aria-pressed", String(button.dataset.res === value));
  });
  // rEFInd uses fixed pixel gaps between tiles even when icon sizes double.
  targets.forEach((target, i) => {
    const system = i < 2;
    const size = (system ? 192 : 48) * scale;
    const center = width / 2 + (system ? (i - 0.5) * (216 * scale + 8) : (i - 4) * (64 * scale + 8));
    const top = system ? height / 2 - size / 2 : height / 2 + 116 * scale + 16;
    Object.assign(target.style, {
      left: (center - size / 2) / width * 100 + "%", top: top / height * 100 + "%",
      width: size / width * 100 + "%", height: size / height * 100 + "%"
    });
  });
  select(selection);
}
document.querySelectorAll("[data-res]").forEach(button => {
  button.onclick = () => setResolution(button.dataset.res);
});
zoom.onclick = () => {
  const native = viewport.classList.toggle("native");
  zoom.setAttribute("aria-pressed", String(native));
  zoom.textContent = native ? "Encajar en pantalla" : "Ver a tamaño real";
  if (native) centerSelection();
};
if (document.fullscreenEnabled) {
  full.hidden = false;
  full.onclick = async () => {
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else await monitor.requestFullscreen();
    } catch {
      document.querySelector("#status").textContent = "Pantalla completa no disponible.";
    }
  };
  document.addEventListener("fullscreenchange", () => {
    full.textContent = document.fullscreenElement ? "Salir de pantalla completa" : "Pantalla completa";
  });
}
document.addEventListener("keydown", event => {
  if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
  const inSystems = selection < 2;
  const start = inSystems ? 0 : 2;
  const count = inSystems ? 2 : 5;
  let next = selection;
  switch (event.key) {
    case "ArrowRight": next = start + (selection - start + 1) % count; break;
    case "ArrowLeft": next = start + (selection - start + count - 1) % count; break;
    case "ArrowDown": next = inSystems ? lastTool : selection; break;
    case "ArrowUp": next = inSystems ? selection : lastSystem; break;
    default: return;
  }
  event.preventDefault();
  select(next);
  if (choices.includes(document.activeElement)) choices[next].focus({preventScroll:true});
});
setResolution(resolution);
