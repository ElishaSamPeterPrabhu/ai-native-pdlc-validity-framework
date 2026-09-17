const UI_OPTIONS = { width: 440, height: 680 };

figma.showUI(__html__, UI_OPTIONS);

function selectedNodeSummary() {
  const node = figma.currentPage.selection[0];
  return node
    ? { id: node.id, name: node.name, type: node.type }
    : null;
}

function sendSelection() {
  figma.ui.postMessage({
    type: "selection",
    node: selectedNodeSummary(),
  });
}

figma.on("selectionchange", sendSelection);
sendSelection();

figma.ui.onmessage = (message) => {
  if (message?.type === "close") {
    figma.closePlugin();
  }
};
