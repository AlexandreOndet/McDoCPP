<script lang="ts">
  import { asset } from '$app/paths';

  const KINDS = new Set(['fries', 'burger', 'coffee', 'drink', 'nuggets', 'hashbrown', 'pie', 'wrap', 'muffin', 'meal', 'fish', 'mcflurry']);
  let { kind, size = 120, label = '' }: { kind: string; size?: number | string; label?: string } = $props();
  const id = $derived(KINDS.has(kind) ? kind : 'burger');
</script>

<svg
  width={size}
  height={size}
  viewBox="0 0 120 120"
  role={label ? 'img' : 'presentation'}
  aria-label={label || undefined}
  aria-hidden={label ? undefined : 'true'}
  class="food"
>
  <use href={`${asset('food.svg')}#${id}`} />
</svg>

<style>
  .food {
    display: block;
    flex: none;
  }
</style>
