const notesEl = document.querySelector<HTMLUListElement>('#notes')!;

async function render() {
  const { notes = [] } = await browser.storage.local.get('notes');
  notesEl.innerHTML = (notes as string[]).map((n) => `<li>${n}</li>`).join('');
}

document.querySelector('#save')!.addEventListener('click', async () => {
  const input = document.querySelector<HTMLInputElement>('#note')!;
  const note = input.value.trim();
  if (!note) return;
  const { notes = [] } = await browser.storage.local.get('notes');
  await browser.storage.local.set({ notes: [...(notes as string[]), note] });
  input.value = '';
  await render();
});

// answer through the background SW to prove messaging works
const pong = await browser.runtime.sendMessage({ type: 'ping' });
document.querySelector('header')!.dataset.pong = pong?.from ?? 'none';

render();
