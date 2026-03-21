import React from "react";

const StrategicDeck = ({ strategies }: { strategies: string[] }) => {
  return (
    <div className="grid grid-cols-2 gap-4">
      {strategies.map((strategy, index) => (
        <div key={index} className="bg-blue-100 p-3 rounded shadow">
          <p>{strategy}</p>
        </div>
      ))}
    </div>
  );
};

export default StrategicDeck;
