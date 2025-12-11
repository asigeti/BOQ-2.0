'use client';

import * as React from 'react';
import { useState } from 'react';
import { useServerInsertedHTML } from 'next/navigation';
import { CacheProvider } from '@emotion/react';
import createCache from '@emotion/cache';
import rtlPlugin from 'stylis-plugin-rtl';
import { prefixer } from 'stylis';

// Create RTL cache
function createEmotionCache() {
  return createCache({
    key: 'muirtl',
    stylisPlugins: [prefixer, rtlPlugin],
    prepend: true,
  });
}

export default function EmotionRegistry({ children }: { children: React.ReactNode }) {
  const [cache] = useState(() => {
    const cache = createEmotionCache();
    cache.compat = true;
    return cache;
  });

  useServerInsertedHTML(() => {
    const entries = Object.entries(cache.inserted);
    if (entries.length === 0) {
      return null;
    }

    let styles = '';
    let dataEmotionAttribute = cache.key;
    const names: string[] = [];

    for (const [name, value] of entries) {
      if (typeof value === 'string') {
        names.push(name);
        styles += value;
      }
    }

    if (names.length > 0) {
      dataEmotionAttribute += ` ${names.join(' ')}`;
    }

    return (
      <style
        key={cache.key}
        data-emotion={dataEmotionAttribute}
        dangerouslySetInnerHTML={{ __html: styles }}
      />
    );
  });

  return <CacheProvider value={cache}>{children}</CacheProvider>;
}
