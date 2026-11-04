import { loadIndex, loadMeta } from '$lib/data';
import type { LayoutLoad } from './$types';

export const prerender = true;
export const ssr = false;

export const load: LayoutLoad = async () => {
  const [meta, index] = await Promise.all([loadMeta(), loadIndex()]);
  return { meta, index };
};
