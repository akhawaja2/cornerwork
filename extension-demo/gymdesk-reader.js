// Read only rendered attendance records. No requests, cookies, or Gymdesk writes.
function readGymdeskAttendance(doc = document, href = location.href) {
  const url = new URL(href);
  if (url.origin !== 'https://app.gymdesk.com' || url.pathname !== '/manager/members/attendance/id/12672454')
    throw Error("Open Sarah Demo's Gymdesk Attendance page, then click the Cornerwork toolbar icon.");
  const name = doc.querySelector('h2.member-name')?.textContent.trim();
  const gym = doc.querySelector('#logo')?.getAttribute('title')?.trim();
  if (name !== 'Sarah Demo' || gym !== 'AKLabs MMA') throw Error('This pilot only imports Sarah Demo at AKLabs MMA.');
  const rows = [...doc.querySelectorAll('tr[attr-id][attr-session][attr-date]')].filter(r => r.getClientRects().length);
  if (!rows.length && !doc.body.innerText.includes('No attendance found.')) throw Error('Attendance is not loaded or the page layout has changed. Refresh Gymdesk and try again.');
  const records = rows.slice(0,100).map(row => {
    const cells = [...row.children];
    const member = cells.find(c => c.hasAttribute('attr-member'));
    if (member?.getAttribute('attr-member') !== '12672454') throw Error('Unexpected member in attendance row.');
    const details = cells.filter(c => !c.hasAttribute('attr-member'));
    const title = details[0]?.querySelector('em')?.textContent.trim();
    const when = details[1]?.querySelector('em')?.textContent.trim();
    const duration = details[1]?.querySelector('small')?.textContent.trim();
    const date = row.getAttribute('attr-date');
    const id = row.getAttribute('attr-id');
    const sessionId = row.getAttribute('attr-session');
    if (!title || !when || !duration || !/^\d+$/.test(id) || !/^\d+$/.test(sessionId)) throw Error('Incomplete attendance record; nothing imported.');
    return {id,sessionId,title,when,duration,date};
  });
  return {memberId:'12672454',memberName:name,gym,records,observedAt:new Date().toISOString()};
}
if (typeof module !== 'undefined') module.exports = readGymdeskAttendance;
