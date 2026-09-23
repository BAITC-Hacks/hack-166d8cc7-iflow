export function Terrain() {
  return <svg className="atlas-terrain" viewBox="0 0 1000 940" preserveAspectRatio="none" aria-hidden="true">
    <defs>
      <pattern id="atlas-grain" width="24" height="24" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1" fill="#3d6a51" opacity=".14"/></pattern>
    </defs>
    <rect width="1000" height="940" fill="#f0f1df"/>
    <path d="M0 100Q180 -25 420 85Q535 235 426 425Q251 560 0 408Z" fill="#cae0ad"/>
    <path d="M0 119Q168 7 397 99Q508 239 400 405Q230 528 0 383" fill="none" stroke="#a8c77e" strokeWidth="2"/>
    <path d="M569 152Q779 72 1000 148V486Q796 556 577 414Q520 278 569 152Z" fill="#d4deed"/>
    <path d="M580 167Q802 105 1000 168M1000 461Q786 522 596 401" fill="none" stroke="#b9c9e0" strokeWidth="2"/>
    <path d="M534 561Q730 440 1000 571V931Q740 980 596 839Q477 698 534 561Z" fill="#f3d6ac"/>
    <path d="M551 578Q735 467 1000 591M1000 907Q751 954 615 825" fill="none" stroke="#dfbd89" strokeWidth="2"/>
    <path d="M0 593Q278 510 425 645Q517 798 364 940H0Z" fill="#c9ddc8"/>
    <path d="M0 614Q264 539 407 658Q488 795 344 940" fill="none" stroke="#abc9ac" strokeWidth="2"/>
    <rect width="1000" height="940" fill="url(#atlas-grain)"/>
    <path d="M470 -30C530 190 410 310 493 466S438 705 513 980" stroke="#d4e5dd" strokeWidth="47" fill="none"/>
    <path d="M470 -30C530 190 410 310 493 466S438 705 513 980" stroke="#b5d2c7" strokeWidth="2" strokeDasharray="8 12" fill="none"/>
    <g fill="none" strokeLinecap="round">
      <path d="M500 852Q392 837 250 686M500 852Q613 826 740 658M250 686Q209 555 260 367M740 658Q804 486 750 338M260 367L260 169M260 367Q489 470 750 338M260 169Q375 116 500 75M750 338Q671 151 500 75" stroke="#fffcf0" strokeWidth="19"/>
      <path d="M500 852Q392 837 250 686M500 852Q613 826 740 658M250 686Q209 555 260 367M740 658Q804 486 750 338M260 367L260 169M260 367Q489 470 750 338M260 169Q375 116 500 75M750 338Q671 151 500 75" stroke="#97ae86" strokeWidth="2" strokeDasharray="4 10"/>
    </g>
    <g fill="#4c8967" stroke="#376e51" strokeWidth="2">
      <path d="M81 320v-40m-22 13 22-50 22 50Zm18-99v-32m-18 10 18-43 18 43ZM864 752v-31m-18 10 18-43 18 43Zm43 22v-39m-22 13 22-50 22 50ZM104 773v-31m-18 10 18-43 18 43Z"/>
    </g>
    <g stroke="#9aab86" fill="none" strokeWidth="2"><ellipse cx="106" cy="443" rx="50" ry="16"/><ellipse cx="106" cy="443" rx="31" ry="8"/><ellipse cx="861" cy="864" rx="52" ry="16"/></g>
    <g fill="#fff9df" stroke="#b7bb91" strokeWidth="2"><path d="m883 222 20-12 20 12v30l-20 12-20-12Z"/><path d="m867 226 36-28 36 28-36 17Z"/><path d="m93 854 28-16 28 16v28l-28 16-28-16Z"/><path d="m81 856 40-35 40 35-40 22Z"/></g>
    <g fill="#d3ac4d"><circle cx="383" cy="324" r="5"/><circle cx="359" cy="340" r="3"/><circle cx="869" cy="590" r="5"/><circle cx="889" cy="605" r="3"/></g>
  </svg>;
}

