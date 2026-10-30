import { useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';

// Counts in-app navigation in GoatCounter (script tag in public/index.html).
// The script counts the first page load itself; window.goatcounter is missing
// when an ad blocker stops the script, so every call is optional.
export const usePageViews = () => {
  const { pathname } = useLocation();
  const firstLoad = useRef(true);

  useEffect(() => {
    if (firstLoad.current) {
      firstLoad.current = false;
      return;
    }
    window.goatcounter?.count?.({ path: pathname });
  }, [pathname]);
};
