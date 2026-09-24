package com.screenmonitor.app.util

import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Date
import java.util.Locale

object TimeUtils {

    private val clockFormat = SimpleDateFormat("HH:mm", Locale.getDefault())
    private val dateFormat = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault())
    private val dateFormatCn = SimpleDateFormat("M月d日 EEEE", Locale.getDefault())

    fun formatClock(ts: Long): String = clockFormat.format(Date(ts))

    fun formatDate(ts: Long): String = dateFormat.format(Date(ts))

    fun formatDateCn(ts: Long): String = dateFormatCn.format(Date(ts))

    fun today(): String = dateFormat.format(Date())

    fun dateToTs(date: String): Long {
        return try {
            dateFormat.parse(date)?.time ?: 0L
        } catch (_: Exception) {
            0L
        }
    }

    fun addDays(date: String, days: Int): String {
        val cal = Calendar.getInstance()
        cal.timeInMillis = dateToTs(date)
        cal.add(Calendar.DAY_OF_YEAR, days)
        return dateFormat.format(cal.time)
    }

    /** 格式化为「X小时Y分钟」或「Y分钟」 */
    fun formatDuration(ms: Long): String {
        val totalMin = ms / 60000
        if (totalMin < 1) return "<1分钟"
        val h = totalMin / 60
        val m = totalMin % 60
        return when {
            h > 0 && m > 0 -> "${h}小时${m}分钟"
            h > 0 -> "${h}小时"
            else -> "${m}分钟"
        }
    }

    /** 秒级显示：X小时Y分Z秒 */
    fun formatDurationDetail(ms: Long): String {
        val totalSec = ms / 1000
        val h = totalSec / 3600
        val m = (totalSec % 3600) / 60
        val s = totalSec % 60
        return when {
            h > 0 -> "${h}小时${m}分${s}秒"
            m > 0 -> "${m}分${s}秒"
            else -> "${s}秒"
        }
    }
}
