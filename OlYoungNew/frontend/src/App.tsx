import { useState } from "react";
import { BottomTabs, type AppTab } from "./components/BottomTabs";
import { HomePage } from "./pages/HomePage";
import { MixPage } from "./pages/MixPage";
import { NewProductsPage } from "./pages/NewProductsPage";

export default function App() {
  const [tab, setTab] = useState<AppTab>("home");
  const [mixIds, setMixIds] = useState<number[]>([]);

  const addToMix = (productId: number) => {
    setMixIds((current) => {
      if (current.includes(productId)) return current;
      return [...current, productId].slice(-4);
    });
  };

  const removeFromMix = (productId: number) => {
    setMixIds((current) => current.filter((id) => id !== productId));
  };

  return (
    <div className="app-frame">
      {tab === "home" && <HomePage mixIds={mixIds} onAddToMix={addToMix} />}
      {tab === "new" && <NewProductsPage mixIds={mixIds} onAddToMix={addToMix} />}
      {tab === "mix" && <MixPage mixIds={mixIds} onRemove={removeFromMix} />}
      <BottomTabs current={tab} mixCount={mixIds.length} onChange={setTab} />
    </div>
  );
}
