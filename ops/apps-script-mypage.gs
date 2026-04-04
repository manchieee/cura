// =====================================================================
// cura 予約システム + マイページ バックエンド
// バージョン: 5 (2026-04-04)
// =====================================================================
// 【セットアップ手順】
// 1. Googleスプレッドシートを新規作成
// 2. そのスプレッドシートのIDをSHEET_IDに設定
//    （URLの /d/〇〇〇/edit の〇〇〇の部分）
// 3. このコードを既存スクリプトに貼り付けて上書き
// 4. 「デプロイ」→「新しいデプロイ」→「ウェブアプリ」
//    アクセス権：全員
// 5. デプロイURLをmypage.htmlのAPPS_SCRIPT_URLに設定
// =====================================================================

var CALENDAR_ID = '45944962c52519825b3d027ea8ad49dc91ea14df582e605e26d3e56cc0c33d75@group.calendar.google.com';
var NOTIFY_EMAIL = 'honeypots.m@gmail.com';
var KEYWORD = '受付可能';
var SHEET_ID = '1w0FJ3HM8JosH-jZqwOpnDvbeNuOqJkWANVt1pQiIayg';

// ─────────────────────────────────────────
// エントリーポイント
// ─────────────────────────────────────────

function doGet(e) {
  var action = e.parameter.action;

  if (action === 'getClient')     return jsonResponse(getClient(e.parameter.token));
  if (action === 'validateToken') return jsonResponse(validateToken(e.parameter.token));
  if (action === 'verifyPin')     return jsonResponse(verifyPin(e.parameter.token, e.parameter.pin));

  // 既存：空き枠取得
  return jsonResponse(getSlots());
}

function doPost(e) {
  var data = JSON.parse(e.postData.contents);
  var action = data.action;

  if (action === 'createReservation') return jsonResponse(createReservation(data));
  if (action === 'cancelReservation') return jsonResponse(cancelReservation(data));
  if (action === 'sendMemo')          return jsonResponse(sendMemo(data));

  // 既存：仮予約（HPの予約フォームから）
  return jsonResponse(book(data));
}

function jsonResponse(obj) {
  var output = ContentService.createTextOutput(JSON.stringify(obj));
  output.setMimeType(ContentService.MimeType.JSON);
  return output;
}

// ─────────────────────────────────────────
// スプレッドシートヘルパー
// ─────────────────────────────────────────

function getSheet(name) {
  var ss = SpreadsheetApp.openById(SHEET_ID);
  var sheet = ss.getSheetByName(name);
  if (!sheet) {
    sheet = ss.insertSheet(name);
    if (name === 'clients') {
      sheet.appendRow(['token', 'name', 'nameShort', 'email', 'phone', 'createdAt', 'pin', 'active', 'expiresAt']);
    } else if (name === 'reservations') {
      sheet.appendRow(['id', 'clientToken', 'date', 'time', 'hours', 'service', 'note', 'status', 'caregiver', 'estimatedCost', 'createdAt']);
    } else if (name === 'memos') {
      sheet.appendRow(['id', 'clientToken', 'text', 'createdAt', 'fromStaff']);
    }
  }
  return sheet;
}

// ─────────────────────────────────────────
// マイページ機能
// ─────────────────────────────────────────

/**
 * トークン有効性チェック（PIN入力前）
 * GET ?action=validateToken&token=xxx
 * 返値: { valid: true } or { valid: false, reason: '...' }
 * ※PINは返さない
 */
function validateToken(token) {
  if (!token) return { valid: false, reason: 'token required' };

  try {
    var sheet = getSheet('clients');
    var rows = sheet.getDataRange().getValues();

    for (var i = 1; i < rows.length; i++) {
      if (rows[i][0] !== token) continue;

      // active チェック（列7、空欄の場合はtrueとみなす）
      var active = rows[i][7];
      if (active === false || active === 'false' || active === 0) {
        return { valid: false, reason: 'inactive' };
      }

      // 有効期限チェック（列8、空欄の場合は無期限）
      var expiresAt = rows[i][8];
      if (expiresAt && expiresAt !== '') {
        var expDate = new Date(expiresAt);
        if (!isNaN(expDate.getTime()) && expDate < new Date()) {
          return { valid: false, reason: 'expired' };
        }
      }

      return { valid: true };
    }

    return { valid: false, reason: 'not found' };
  } catch (e) {
    return { valid: false, reason: e.message };
  }
}

/**
 * PIN認証＋クライアントデータ返却
 * GET ?action=verifyPin&token=xxx&pin=1234
 * 返値: { success: true, clientData: {...} } or { success: false }
 */
function verifyPin(token, pin) {
  if (!token || !pin) return { success: false };

  try {
    var sheet = getSheet('clients');
    var rows = sheet.getDataRange().getValues();

    for (var i = 1; i < rows.length; i++) {
      if (rows[i][0] !== token) continue;

      // active・有効期限チェック
      var active = rows[i][7];
      if (active === false || active === 'false' || active === 0) {
        return { success: false, reason: 'inactive' };
      }
      var expiresAt = rows[i][8];
      if (expiresAt && expiresAt !== '') {
        var expDate = new Date(expiresAt);
        if (!isNaN(expDate.getTime()) && expDate < new Date()) {
          return { success: false, reason: 'expired' };
        }
      }

      // PIN照合（列6）
      var storedPin = String(rows[i][6]).trim();
      if (storedPin !== String(pin).trim()) {
        return { success: false, reason: 'wrong pin' };
      }

      // 認証成功 → getClientと同じデータを返す
      var clientData = getClient(token);
      return { success: true, clientData: clientData };
    }

    return { success: false, reason: 'not found' };
  } catch (e) {
    return { success: false, reason: e.message };
  }
}

/**
 * クライアントデータ取得
 * GET ?action=getClient&token=xxx
 */
function getClient(token) {
  if (!token) return { error: 'token required' };

  try {
    // クライアント検索
    var clientSheet = getSheet('clients');
    var clientRows = clientSheet.getDataRange().getValues();
    var client = null;

    for (var i = 1; i < clientRows.length; i++) {
      if (clientRows[i][0] === token) {
        client = {
          name:      clientRows[i][1],
          nameShort: clientRows[i][2],
          email:     clientRows[i][3],
          phone:     clientRows[i][4]
        };
        break;
      }
    }

    if (!client) return { error: 'client not found' };

    // 予約取得（今日以降＝upcoming、過去＝history）
    var resSheet = getSheet('reservations');
    var resRows = resSheet.getDataRange().getValues();
    var reservations = [];
    var history = [];
    var today = new Date();
    today.setHours(0, 0, 0, 0);

    for (var j = 1; j < resRows.length; j++) {
      if (resRows[j][1] !== token) continue;
      var resDate = new Date(resRows[j][2]);
      var item = {
        id:            resRows[j][0],
        date:          resRows[j][2],
        time:          resRows[j][3],
        hours:         resRows[j][4],
        service:       resRows[j][5],
        note:          resRows[j][6],
        status:        resRows[j][7],
        caregiver:     resRows[j][8],
        estimatedCost: resRows[j][9]
      };
      if (resDate >= today && resRows[j][7] !== 'cancelled') {
        reservations.push(item);
      } else {
        history.push(item);
      }
    }

    // メモ取得
    var memoSheet = getSheet('memos');
    var memoRows = memoSheet.getDataRange().getValues();
    var memos = [];

    for (var k = 1; k < memoRows.length; k++) {
      if (memoRows[k][1] !== token) continue;
      memos.push({
        id:        memoRows[k][0],
        text:      memoRows[k][2],
        createdAt: memoRows[k][3],
        fromStaff: memoRows[k][4]
      });
    }

    // ソート
    reservations.sort(function(a, b) { return new Date(a.date) - new Date(b.date); });
    history.sort(function(a, b)      { return new Date(b.date) - new Date(a.date); });
    memos.sort(function(a, b)        { return new Date(b.createdAt) - new Date(a.createdAt); });

    return {
      name:         client.name,
      nameShort:    client.nameShort,
      email:        client.email,
      phone:        client.phone,
      reservations: reservations,
      history:      history,
      memos:        memos
    };

  } catch(err) {
    return { error: err.toString() };
  }
}

/**
 * 予約リクエスト作成
 * POST { action, token, date, time, hours, service, note }
 */
function createReservation(data) {
  if (!data.token) return { error: 'token required' };

  try {
    var lock = LockService.getScriptLock();
    lock.waitLock(10000);

    var sheet = getSheet('reservations');
    var id  = 'res_' + new Date().getTime();
    var now = new Date().toISOString();
    var cost = calcRate(data.time, data.hours);

    sheet.appendRow([
      id,
      data.token,
      data.date,
      data.time,
      data.hours,
      data.service || 'プライベートケア',
      data.note    || '',
      '仮予約',
      '',
      cost,
      now
    ]);

    // ── カレンダー同期 ──
    var calEventId = '';
    try {
      var cal = CalendarApp.getCalendarById(CALENDAR_ID);
      var startDt = new Date(data.date + 'T' + (data.time || '10:00') + ':00+09:00');
      var endDt   = new Date(startDt.getTime() + (parseInt(data.hours) || 3) * 60 * 60 * 1000);

      // 重複する「受付可能」枠を削除
      var overlap = cal.getEvents(startDt, endDt);
      for (var ei = 0; ei < overlap.length; ei++) {
        if (overlap[ei].getTitle().indexOf(KEYWORD) !== -1) {
          overlap[ei].deleteEvent();
        }
      }

      // 仮予約イベントを作成してIDを保存
      var clientName = getClientName(data.token);
      var ev = cal.createEvent(
        '[仮予約] ' + clientName + ' 様（マイページ）',
        startDt, endDt,
        { description: 'サービス: ' + (data.service || 'プライベートケア') + '\n備考: ' + (data.note || 'なし') + '\n予約ID: ' + id }
      );
      calEventId = ev.getId();

      // カレンダーイベントIDをSheets reservationsに記録（caregiver列を一時流用）
      var lastRow = sheet.getLastRow();
      sheet.getRange(lastRow, 9).setValue('calEvent:' + calEventId);
    } catch(calErr) {
      Logger.log('Calendar sync failed: ' + calErr);
    }

    lock.releaseLock();

    // 通知メール（まさみ宛）
    var clientName = getClientName(data.token);
    GmailApp.sendEmail(
      NOTIFY_EMAIL,
      '[cura] 予約リクエスト: ' + clientName + ' 様',
      '日付: '    + data.date + '\n' +
      '時間: '    + data.time + '\n' +
      '時間数: '  + data.hours + 'h\n' +
      'サービス: ' + (data.service || 'プライベートケア') + '\n' +
      '備考: '    + (data.note || 'なし') + '\n\n' +
      '概算: ¥'   + cost.toLocaleString()
    );

    return { success: true, id: id, estimatedCost: cost };

  } catch(err) {
    return { error: err.toString() };
  }
}

/**
 * 予約キャンセル
 * POST { action, token, id }
 */
function cancelReservation(data) {
  if (!data.token || !data.id) return { error: 'token and id required' };

  try {
    var sheet = getSheet('reservations');
    var rows = sheet.getDataRange().getValues();

    for (var i = 1; i < rows.length; i++) {
      if (rows[i][0] === data.id && rows[i][1] === data.token) {
        sheet.getRange(i + 1, 8).setValue('cancelled');

        // カレンダーの仮予約イベントも削除
        try {
          var caregiverCell = rows[i][8] ? String(rows[i][8]) : '';
          if (caregiverCell.indexOf('calEvent:') === 0) {
            var calId = caregiverCell.replace('calEvent:', '');
            var cal = CalendarApp.getCalendarById(CALENDAR_ID);
            var ev = cal.getEventById(calId);
            if (ev) ev.deleteEvent();
          }
        } catch(calErr) {
          Logger.log('Calendar cancel sync failed: ' + calErr);
        }

        var clientName = getClientName(data.token);
        GmailApp.sendEmail(
          NOTIFY_EMAIL,
          '[cura] 予約キャンセル: ' + clientName + ' 様',
          '予約ID: ' + data.id + '\n' +
          '日付: '   + rows[i][2] + ' ' + rows[i][3]
        );

        return { success: true };
      }
    }

    return { error: 'reservation not found' };

  } catch(err) {
    return { error: err.toString() };
  }
}

/**
 * メモ・相談送信
 * POST { action, token, text }
 */
function sendMemo(data) {
  if (!data.token || !data.text) return { error: 'token and text required' };

  try {
    var sheet = getSheet('memos');
    var id  = 'memo_' + new Date().getTime();
    var now = new Date().toISOString();

    sheet.appendRow([id, data.token, data.text, now, false]);

    var clientName = getClientName(data.token);
    GmailApp.sendEmail(
      NOTIFY_EMAIL,
      '[cura] メモ/相談: ' + clientName + ' 様',
      data.text + '\n\n送信日時: ' + Utilities.formatDate(new Date(), 'Asia/Tokyo', 'yyyy/MM/dd HH:mm')
    );

    return { success: true, id: id };

  } catch(err) {
    return { error: err.toString() };
  }
}

// ─────────────────────────────────────────
// ユーティリティ
// ─────────────────────────────────────────

/**
 * 料金計算（税込）
 * 〜8時: ¥19,500/h  8〜18時: ¥15,000/h  18〜21時: ¥18,000/h  21時〜: ¥19,500/h
 */
function calcRate(time, hours) {
  var h = parseInt(hours) || 3;
  var hourInt = parseInt((time || '10:00').split(':')[0]);
  var rate = 15000;
  if      (hourInt < 8)  rate = 19500;
  else if (hourInt >= 21) rate = 19500;
  else if (hourInt >= 18) rate = 18000;
  return rate * h;
}

/** クライアント名取得 */
function getClientName(token) {
  try {
    var rows = getSheet('clients').getDataRange().getValues();
    for (var i = 1; i < rows.length; i++) {
      if (rows[i][0] === token) return rows[i][1];
    }
  } catch(e) {}
  return '不明';
}

// ─────────────────────────────────────────
// 既存機能（変更なし）
// ─────────────────────────────────────────

function getSlots() {
  try {
    var cal = CalendarApp.getCalendarById(CALENDAR_ID);
    var now = new Date();
    var end = new Date(now.getTime() + 60 * 24 * 60 * 60 * 1000);
    var events = cal.getEvents(now, end);
    var slots = [];
    for (var i = 0; i < events.length; i++) {
      var ev = events[i];
      if (ev.getTitle().indexOf(KEYWORD) !== -1) {
        slots.push({
          id:    ev.getId(),
          start: ev.getStartTime().toISOString(),
          end:   ev.getEndTime().toISOString()
        });
      }
    }
    return { success: true, slots: slots };
  } catch(e) {
    return { success: false, message: e.toString() };
  }
}

function book(data) {
  try {
    var lock = LockService.getScriptLock();
    lock.waitLock(10000);

    var cal = CalendarApp.getCalendarById(CALENDAR_ID);
    var now = new Date();
    var end = new Date(now.getTime() + 60 * 24 * 60 * 60 * 1000);
    var events = cal.getEvents(now, end);
    var target = null;
    for (var i = 0; i < events.length; i++) {
      if (events[i].getId() === data.slotId) {
        target = events[i];
        break;
      }
    }
    if (!target) {
      lock.releaseLock();
      return { success: false, message: 'この時間はすでに埋まっています。' };
    }
    var start = target.getStartTime();
    var end2  = target.getEndTime();
    target.deleteEvent();
    var desc = '氏名: ' + data.name + '\n電話: ' + data.phone + '\nメール: ' + data.email + '\n相談: ' + data.inquiry;
    cal.createEvent('[仮予約] ' + data.name + ' 様', start, end2, { description: desc });
    lock.releaseLock();

    var d = Utilities.formatDate(start, 'Asia/Tokyo', 'yyyy/MM/dd HH:mm');
    GmailApp.sendEmail(NOTIFY_EMAIL, '[cura] 仮予約: ' + data.name + ' 様', '日時: ' + d + '\n\n' + desc);
    return { success: true };
  } catch(e) {
    return { success: false, message: e.toString() };
  }
}
